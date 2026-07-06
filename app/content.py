"""Découverte et chargement du contenu pédagogique depuis ``app/content/``.

Le moteur est totalement agnostique du contenu. Un chapitre = un sous-dossier :

    chapitre.json    (obligatoire)  métadonnées — voir models.ChapitreMeta
    theorie.md       (optionnel)    théorie en Markdown
    exercices.json   (optionnel)    liste d'exercices — voir models.Exercice
    projet.json      (optionnel)    projet guidé — voir models.Projet

Ajouter un chapitre = ajouter un dossier. Aucun code à modifier.
Le contenu est relu à chaque requête : modifier un fichier puis recharger
la page suffit (pas de redémarrage du serveur).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .models import Chapitre, ChapitreMeta, Exercice, Projet

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


def charger_chapitres() -> tuple[list[Chapitre], list[str]]:
    """Charge tous les chapitres valides, triés par numéro.

    Les dossiers invalides ne bloquent pas l'application : leurs erreurs
    sont retournées à part pour être affichées sur la page d'accueil
    (utile pendant la rédaction de contenu).
    """
    chapitres: list[Chapitre] = []
    erreurs: list[str] = []
    if not CONTENT_DIR.exists():
        return [], [f"Dossier de contenu introuvable : {CONTENT_DIR}"]
    for dossier in sorted(CONTENT_DIR.iterdir()):
        if not dossier.is_dir() or not (dossier / "chapitre.json").exists():
            continue
        try:
            chapitres.append(_charger_dossier(dossier))
        except ErreurContenu as exc:
            erreurs.append(f"{dossier.name} : {exc}")
    chapitres.sort(key=lambda c: c.meta.numero)
    return chapitres, erreurs


def obtenir_chapitre(slug: str) -> Optional[Chapitre]:
    """Charge un chapitre par slug (nom de dossier).

    Retourne ``None`` si le chapitre n'existe pas. Lève ``ErreurContenu``
    s'il existe mais que son contenu est invalide (erreur d'édition à
    remonter clairement plutôt qu'un 404 trompeur).
    """
    dossier = (CONTENT_DIR / slug).resolve()
    # Garde-fou contre la traversée de chemin : le dossier résolu doit
    # être un enfant direct de CONTENT_DIR.
    if dossier.parent != CONTENT_DIR.resolve():
        return None
    if not dossier.is_dir() or not (dossier / "chapitre.json").exists():
        return None
    return _charger_dossier(dossier)
