"""Agent tooling regressions using only temporary files and metadata."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agents import sync_agents, validate_course_skeleton


class TemporaryFiles(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_json(self, relative, data):
        return self.write(relative, json.dumps(data))


class SyncAgentsTests(TemporaryFiles):
    def run_sync(self, *arguments):
        output = io.StringIO()
        with (
            patch.object(sync_agents, "ROOT", self.root),
            patch("sys.argv", ["sync_agents.py", *arguments]),
            redirect_stdout(output),
            redirect_stderr(output),
        ):
            sync_agents.main()
        return output.getvalue()

    def test_discovers_all_sources_and_preserves_client_frontmatter(self):
        headers = {
            ".claude/agents/{name}.md": "---\nname: {name}\nmodel: inherit\n---\n",
            ".github/agents/{name}.agent.md": "---\ndescription: {name}\ntarget: vscode\n---\n",
        }
        adapters = []
        for name in ("architecte-cours", "redacteur-chapitre", "future-agent"):
            self.write(f"agents/{name}.source.md", f"\n# {name}\n\nShared body.\n")
            for pattern, template in headers.items():
                header = template.format(name=name)
                path = self.write(pattern.format(name=name), header + "\nOld body.\n")
                adapters.append((path, header + f"\n# {name}\n\nShared body.\n"))
        self.write("agents/not-a-source.md", "Ignored.")
        orphan = self.write(".claude/agents/orphan.md", "No matching source.")

        self.run_sync()

        for path, expected in adapters:
            self.assertEqual(path.read_text(encoding="utf-8"), expected)
        self.assertEqual(orphan.read_text(encoding="utf-8"), "No matching source.")
        self.assertEqual(self.run_sync(), "")
        self.assertIn("match", self.run_sync("--check"))

    def test_missing_adapters_are_silently_skipped(self):
        self.write("agents/without-clients.source.md", "# No clients\n")
        self.write("agents/claude-only.source.md", "# Claude\n")
        self.write(".claude/agents/claude-only.md", "---\nmodel: inherit\n---\n")
        self.write("agents/copilot-only.source.md", "# Copilot\n")
        self.write(".github/agents/copilot-only.agent.md", "---\ntarget: vscode\n---\n")
        output = self.run_sync()
        self.assertNotIn("without-clients", output)
        self.assertFalse((self.root / ".github/agents/claude-only.agent.md").exists())
        self.assertFalse((self.root / ".claude/agents/copilot-only.md").exists())
        self.assertFalse((self.root / ".claude/agents/without-clients.md").exists())
        self.run_sync("--check")

    def test_check_exits_one_without_writing_then_accepts_synchronized_body(self):
        self.write("agents/test.source.md", "# New\n")
        adapter = self.write(".claude/agents/test.md", "---\nmodel: inherit\n---\n\nOld\n")
        before = adapter.read_bytes()
        with self.assertRaises(SystemExit) as raised:
            self.run_sync("--check")
        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(adapter.read_bytes(), before)
        self.run_sync()
        self.run_sync("--check")

    def test_invalid_sources_or_frontmatters_do_not_partially_write(self):
        self.write("agents/first.source.md", "# First\n")
        first = self.write(".claude/agents/first.md", "---\nmodel: inherit\n---\n\nOld\n")
        self.write("agents/last.source.md", "# Last\n")
        before = first.read_bytes()
        for body in ("No header", "---\nUnclosed header\n"):
            with self.subTest(body=body):
                self.write(".claude/agents/last.md", body)
                with self.assertRaises(ValueError):
                    self.run_sync()
                self.assertEqual(first.read_bytes(), before)
        self.write("agents/last.source.md", " \n")
        with self.assertRaisesRegex(ValueError, "Empty agent source"):
            self.run_sync()
        self.assertEqual(first.read_bytes(), before)


class CourseSkeletonTests(TemporaryFiles):
    def setUp(self):
        super().setUp()
        self.content = self.root / "content"
        replacement = patch("app.content.CONTENT_DIR", self.content)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.course = {
            "ordre": 1, "titre": "Example", "description": "A course.",
            "icone": "X", "statut": "a_venir",
        }
        self.chapter = {
            "numero": 0, "titre": "Setup", "description": "Initial setup.",
            "objectifs": ["Prepare an environment."],
            "points_theorie": ["Environment configuration."],
            "projets_cibles": ["Tous"], "statut": "squelette",
        }
        self.write_json("content/example/cours.json", self.course)
        self.write_json("content/example/chapitre_00_setup/chapitre.json", self.chapter)

    def validate(self, course="example"):
        with redirect_stdout(io.StringIO()):
            validate_course_skeleton.validate_course_skeleton(course)

    def test_metadata_only_without_loading_or_requiring_lesson_documents(self):
        before = {
            path: path.read_bytes() for path in self.content.rglob("*") if path.is_file()
        }
        with patch("app.content.obtenir_chapitre", side_effect=AssertionError("Full loader")):
            self.validate()
            for name in ("theorie.md", "exercices.json", "projet.json"):
                self.write(f"content/example/chapitre_00_setup/{name}", "Invalid lesson data")
            self.validate()
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)

    def test_numbers_are_unique_within_course_only(self):
        self.write_json("content/another/cours.json", self.course)
        self.write_json("content/another/chapitre_00_setup/chapitre.json", self.chapter)
        self.validate()
        self.validate("another")
        self.write_json("content/example/duplicate/chapitre.json", self.chapter)
        with self.assertRaisesRegex(ValueError, "duplicate chapter number"):
            self.validate()

    def test_exact_fields_and_strict_models_for_both_metadata_types(self):
        cases = (
            ("cours.json", self.course, "ordre"),
            ("chapitre_00_setup/chapitre.json", self.chapter, "numero"),
        )
        for filename, original, number_key in cases:
            missing = dict(original)
            del missing["description"]
            invalid_cases = (
                [], missing, {**original, "narration": "Extra field"},
                {**original, number_key: "0"}, {**original, number_key: True},
                {**original, "statut": "unknown"}, {**original, "titre": " "},
            )
            for data in invalid_cases:
                with self.subTest(filename=filename, data=data):
                    self.write_json(f"content/example/{filename}", data)
                    with self.assertRaises(ValueError):
                        self.validate()
            self.write_json(f"content/example/{filename}", original)

    def test_targets_objectives_outline_and_non_negative_number(self):
        for targets in ([], ["ESP32"], ["Tous", "Cuisine"], ["Enduro", "Enduro"], [" "]):
            with self.subTest(targets=targets):
                self.write_json(
                    "content/example/chapitre_00_setup/chapitre.json",
                    {**self.chapter, "projets_cibles": targets},
                )
                with self.assertRaises(ValueError):
                    self.validate()
        for field, value in (
            ("numero", -1), ("objectifs", []), ("points_theorie", []),
            ("objectifs", [" "]), ("points_theorie", [""]),
        ):
            with self.subTest(field=field, value=value):
                self.write_json(
                    "content/example/chapitre_00_setup/chapitre.json",
                    {**self.chapter, field: value},
                )
                with self.assertRaises(ValueError):
                    self.validate()
        for targets in (["Tous"], ["Cuisine"], ["Finance", "Enduro"], ["Cuisine", "Finance", "Enduro"]):
            self.write_json(
                "content/example/chapitre_00_setup/chapitre.json",
                {**self.chapter, "projets_cibles": targets},
            )
            self.validate()

    def test_missing_or_malformed_metadata_and_empty_course_fail(self):
        path = self.content / "example/cours.json"
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.validate()
        path.write_text("{", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.validate()
        self.write_json("content/example/cours.json", self.course)
        chapter_path = self.content / "example/chapitre_00_setup/chapitre.json"
        chapter_path.write_text("{", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            self.validate()
        chapter_path.unlink()
        with self.assertRaisesRegex(ValueError, "missing chapter metadata"):
            self.validate()

    def test_rejects_non_direct_courses_and_escaping_chapter_links(self):
        for slug in ("", ".", "..", "../content/example", str(self.content / "example"), "unknown"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                self.validate(slug)
        self.write_json("outside/cours.json", self.course)
        (self.content / "linked").symlink_to(self.root / "outside", target_is_directory=True)
        with self.assertRaises(ValueError):
            self.validate("linked")
        self.write_json("outside/chapitre.json", {**self.chapter, "numero": 1})
        (self.content / "example/linked").symlink_to(self.root / "outside", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "direct child"):
            self.validate()

    def test_accepts_partially_written_course_metadata_and_cli_argument(self):
        self.write_json(
            "content/example/chapitre_01_next/chapitre.json",
            {**self.chapter, "numero": 1, "statut": "complet"},
        )
        with (
            patch("sys.argv", ["validate_course_skeleton.py", "example"]),
            redirect_stdout(io.StringIO()) as output,
        ):
            validate_course_skeleton.main()
        self.assertIn("2 chapters", output.getvalue())


if __name__ == "__main__":
    unittest.main()
