"""Synchronize the shared agent body without changing client frontmatter."""

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    updates = []
    for source in sorted((ROOT / "agents").glob("*.source.md")):
        body = source.read_text(encoding="utf-8").strip() + "\n"
        if not body.strip():
            raise ValueError(f"Empty agent source: {source}")
        name = source.name.removesuffix(".source.md")
        adapters = (
            ROOT / ".claude" / "agents" / f"{name}.md",
            ROOT / ".github" / "agents" / f"{name}.agent.md",
        )
        for path in adapters:
            if not path.exists():
                continue
            current = path.read_text(encoding="utf-8")
            if not current.startswith("---\n"):
                raise ValueError(f"Missing YAML frontmatter: {path}")
            header, separator, _ = current[4:].partition("\n---\n")
            if not separator:
                raise ValueError(f"Unclosed YAML frontmatter: {path}")
            expected = f"---\n{header}\n---\n\n{body}"
            if current != expected:
                updates.append((path, expected))

    if args.check:
        if updates:
            parser.exit(1, "Agent bodies differ; run python3 agents/sync_agents.py\n")
        print("All existing adapter bodies match their shared sources.")
    else:
        for path, expected in updates:
            path.write_text(expected, encoding="utf-8")
            print(f"Updated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
