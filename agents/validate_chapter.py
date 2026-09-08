"""Validate chapter documents, never execute their embedded code.

Run from the repository root: python -m agents.validate_chapter <cours> <slug>
Example: python -m agents.validate_chapter python chapitre_01_fondamentaux
Chapter numbers must be unique within their course, not across all courses.
"""

import argparse
import json

from app.content import CONTENT_DIR, obtenir_chapitre, obtenir_cours_meta
from app.models import ChapitreMeta, Exercice, Projet, Ressource


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_object(data, model, label):
    require(isinstance(data, dict), f"{label}: expected an object")
    require(set(data) == set(model.model_fields), f"{label}: unexpected or missing fields")
    result = model.model_validate(data, strict=True)
    for key, value in data.items():
        if isinstance(value, str):
            require(bool(value.strip()), f"{label}.{key}: empty text")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    require(bool(item.strip()), f"{label}.{key}: empty item")
    if "ressources" in data:
        require(bool(data["ressources"]), f"{label}: missing resources")
        for resource in data["ressources"]:
            validate_object(resource, Ressource, f"{label}.ressources")
            require(
                resource["url"].startswith(("https://", "http://")),
                f"{label}: resource URL must use HTTP(S)",
            )
        require(2 <= len(data["indices"]) <= 3, f"{label}: expected 2 to 3 hints")
    return result


def validate_chapter(cours, slug):
    require(obtenir_cours_meta(cours) is not None, "Unknown or invalid course")
    course_folder = CONTENT_DIR / cours
    folder = course_folder / slug
    require(
        folder.resolve().parent == course_folder.resolve() and folder.name == slug,
        "The slug must identify a direct child of app/content/<cours>",
    )

    def load(filename):
        with (folder / filename).open(encoding="utf-8") as source:
            return json.load(source)

    meta = validate_object(load("chapitre.json"), ChapitreMeta, "chapitre.json")
    require(meta.numero >= 0, "Chapter number must be non-negative")
    require(bool(meta.objectifs), "Missing chapter objectives")
    targets = meta.projets_cibles
    require(
        targets == ["Tous"]
        or (
            bool(targets)
            and len(targets) == len(set(targets))
            and set(targets) <= {"Cuisine", "Finance", "Enduro"}
        ),
        "Invalid projets_cibles",
    )
    for other in course_folder.glob("*/chapitre.json"):
        if other.parent.resolve() != folder.resolve():
            with other.open(encoding="utf-8") as source:
                other_meta = json.load(source)
            require(other_meta["numero"] != meta.numero, f"Duplicate chapter number: {other}")

    theory = (folder / "theorie.md").read_text(encoding="utf-8")
    require(any(line.startswith("## ") for line in theory.splitlines()), "Missing theory sections")
    exercises = load("exercices.json")
    require(isinstance(exercises, list), "exercices.json: expected a list")
    require(4 <= len(exercises) <= 6, "Expected 4 to 6 exercises")
    ids = []
    for index, exercise in enumerate(exercises):
        parsed = validate_object(exercise, Exercice, f"exercise {index + 1}")
        ids.append(parsed.id)
    require(len(ids) == len(set(ids)), "Duplicate exercise IDs")
    project = validate_object(load("projet.json"), Projet, "projet.json")
    require(bool(project.etapes), "Missing project steps")

    chapter = obtenir_chapitre(cours, slug)
    require(chapter is not None, "The application cannot load the chapter")
    print(f"{cours}/{slug}: documents valid ({len(ids)} exercises, status={meta.statut}).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cours")
    parser.add_argument("slug")
    args = parser.parse_args()
    validate_chapter(args.cours, args.slug)


if __name__ == "__main__":
    main()
