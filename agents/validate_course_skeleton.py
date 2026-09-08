"""Validate course and chapter metadata, never execute their embedded code.

Run from the repository root: python -m agents.validate_course_skeleton <cours>
No theory, exercise or project documents are required or loaded.
"""

import argparse
import json

from app import content
from app.models import ChapitreMeta, CoursMeta
from agents.validate_chapter import require, validate_object


def validate_course_skeleton(cours):
    folder = content._dossier_enfant(content.CONTENT_DIR, cours)
    require(folder is not None, "The course must be a direct child of app/content")

    def load(path, model):
        with path.open(encoding="utf-8") as source:
            return validate_object(json.load(source), model, str(path.relative_to(folder)))

    course_meta = load(folder / "cours.json", CoursMeta)
    metadata_paths = sorted(folder.glob("*/chapitre.json"))
    require(bool(metadata_paths), f"{cours}: missing chapter metadata")
    numbers = set()
    for path in metadata_paths:
        require(
            content._dossier_enfant(folder, path.parent.name) is not None,
            f"{path.parent.name}: the chapter must be a direct child of its course",
        )
        meta = load(path, ChapitreMeta)
        label = f"{cours}/{path.parent.name}"
        require(meta.numero >= 0, f"{label}: chapter number must be non-negative")
        require(meta.numero not in numbers, f"{label}: duplicate chapter number {meta.numero}")
        numbers.add(meta.numero)
        require(bool(meta.objectifs), f"{label}: missing chapter objectives")
        require(bool(meta.points_theorie), f"{label}: missing theory outline")
        targets = meta.projets_cibles
        require(
            targets == ["Tous"]
            or (
                bool(targets)
                and len(targets) == len(set(targets))
                and set(targets) <= {"Cuisine", "Finance", "Enduro"}
            ),
            f"{label}: invalid projets_cibles",
        )

    print(f"{cours}: metadata valid ({len(numbers)} chapters, status={course_meta.statut}).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cours")
    args = parser.parse_args()
    validate_course_skeleton(args.cours)


if __name__ == "__main__":
    main()
