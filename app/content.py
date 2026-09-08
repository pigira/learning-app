"""Découverte et chargement du contenu pédagogique depuis ``app/content/``.

Le moteur est totalement agnostique du contenu. Un cours = un sous-dossier
avec ``cours.json``. Chaque chapitre est un sous-dossier de ce cours :

    chapitre.json    (obligatoire)  métadonnées — voir models.ChapitreMeta
    theorie.md       (optionnel)    théorie en Markdown
    exercices.json   (optionnel)    liste d'exercices — voir models.Exercice
    projet.json      (optionnel)    projet guidé — voir models.Projet

Ajouter un cours ou un chapitre = ajouter un dossier. Aucun code à modifier.
Le contenu est relu à chaque requête : modifier un fichier puis recharger
la page suffit (pas de redémarrage du serveur).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .models import Chapitre, ChapitreMeta, Cours, CoursMeta, Exercice, Projet

CONTENT_DIR = Path(__file__).resolve().parent / "content"


class ErreurContenu(Exception):
    """Fichier de contenu manquant, mal formé ou hors schéma."""


def _lire_json(chemin: Path) -> object:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ErreurContenu(f"{chemin.name} : JSON invalide ({exc})") from exc


def _charger_dossier(dossier: Path) -> Chapitre:
    try:
        brut_meta = _lire_json(dossier / "chapitre.json")
        if not isinstance(brut_meta, dict):
            raise ErreurContenu("chapitre.json doit contenir un objet JSON")
        meta = ChapitreMeta(**brut_meta)

        theorie = ""
        chemin_theorie = dossier / "theorie.md"
        if chemin_theorie.exists():
            theorie = chemin_theorie.read_text(encoding="utf-8")

        exercices: list[Exercice] = []
        chemin_ex = dossier / "exercices.json"
        if chemin_ex.exists():
            brut_ex = _lire_json(chemin_ex)
            if not isinstance(brut_ex, list):
                raise ErreurContenu("exercices.json doit contenir une liste")
            exercices = [Exercice(**e) for e in brut_ex]

        projet: Optional[Projet] = None
        chemin_projet = dossier / "projet.json"
        if chemin_projet.exists():
            brut_projet = _lire_json(chemin_projet)
            if not isinstance(brut_projet, dict):
                raise ErreurContenu("projet.json doit contenir un objet JSON")
            projet = Projet(**brut_projet)
    except ValidationError as exc:
        raise ErreurContenu(f"schéma invalide — {exc}") from exc

    return Chapitre(
        slug=dossier.name,
        meta=meta,
        theorie=theorie,
        exercices=exercices,
        projet=projet,
    )


def _dossier_enfant(racine: Path, slug: str) -> Optional[Path]:
    """Résout un slug uniquement vers un dossier enfant direct de la racine."""
    if not slug or Path(slug).name != slug:
        return None
    dossier = (racine / slug).resolve()
    if dossier.parent != racine.resolve() or not dossier.is_dir():
        return None
    return dossier


def obtenir_cours_meta(cours_slug: str) -> Optional[CoursMeta]:
    """Lit uniquement les métadonnées ; signale un contenu présent mais invalide."""
    dossier = _dossier_enfant(CONTENT_DIR, cours_slug)
    if dossier is None or not (dossier / "cours.json").is_file():
        return None
    try:
        brut_meta = _lire_json(dossier / "cours.json")
        if not isinstance(brut_meta, dict):
            raise ErreurContenu("cours.json doit contenir un objet JSON")
        return CoursMeta(**brut_meta)
    except ValidationError as exc:
        raise ErreurContenu(f"cours.json : schéma invalide — {exc}") from exc
    except (OSError, UnicodeError) as exc:
        raise ErreurContenu(f"cours.json : lecture impossible — {exc}") from exc


def charger_cours() -> tuple[list[Cours], list[str]]:
    """Charge les cours et leurs chapitres, triés par ordre, avec leurs erreurs."""
    cours: list[Cours] = []
    erreurs: list[str] = []
    if not CONTENT_DIR.exists():
        return [], [f"Dossier de contenu introuvable : {CONTENT_DIR}"]
    for dossier in sorted(CONTENT_DIR.iterdir()):
        if not dossier.is_dir() or not (dossier / "cours.json").exists():
            continue
        try:
            meta = obtenir_cours_meta(dossier.name)
            if meta is None:
                raise ErreurContenu("dossier de cours ou cours.json inaccessible")
            chapitres, erreurs_chapitres = charger_chapitres(dossier.name)
            cours.append(Cours(slug=dossier.name, meta=meta, chapitres=chapitres))
            erreurs.extend(erreurs_chapitres)
        except ErreurContenu as exc:
            erreurs.append(f"{dossier.name} : {exc}")
    cours.sort(key=lambda c: c.meta.ordre)
    return cours, erreurs


def charger_chapitres(cours_slug: str) -> tuple[list[Chapitre], list[str]]:
    """Charge les chapitres valides d'un cours, triés par numéro.

    Les dossiers invalides ne bloquent pas l'application : leurs erreurs
    sont retournées à part pour être affichées sur la page d'accueil
    (utile pendant la rédaction de contenu).
    """
    chapitres: list[Chapitre] = []
    erreurs: list[str] = []
    dossier_cours = _dossier_enfant(CONTENT_DIR, cours_slug)
    if dossier_cours is None or not (dossier_cours / "cours.json").is_file():
        return [], [f"Cours introuvable : {cours_slug}"]
    for dossier in sorted(dossier_cours.iterdir()):
        if not dossier.is_dir() or not (dossier / "chapitre.json").exists():
            continue
        try:
            chapitre = obtenir_chapitre(cours_slug, dossier.name)
            if chapitre is None:
                raise ErreurContenu("dossier de chapitre inaccessible")
            chapitres.append(chapitre)
        except ErreurContenu as exc:
            erreurs.append(f"{cours_slug}/{dossier.name} : {exc}")
    chapitres.sort(key=lambda c: c.meta.numero)
    return chapitres, erreurs


def obtenir_chapitre(cours_slug: str, slug: str) -> Optional[Chapitre]:
    """Charge un chapitre par slugs de cours et de chapitre (noms de dossiers).

    Retourne ``None`` si le chapitre n'existe pas. Lève ``ErreurContenu``
    s'il existe mais que son contenu est invalide (erreur d'édition à
    remonter clairement plutôt qu'un 404 trompeur).
    """
    dossier_cours = _dossier_enfant(CONTENT_DIR, cours_slug)
    if dossier_cours is None or not (dossier_cours / "cours.json").is_file():
        return None
    dossier = _dossier_enfant(dossier_cours, slug)
    if dossier is None or not (dossier / "chapitre.json").exists():
        return None
    return _charger_dossier(dossier)
