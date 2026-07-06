"""Modèles Pydantic : schéma du contenu pédagogique et payloads de l'API.

Ces modèles définissent le contrat des fichiers JSON de ``app/content/``.
Tout chapitre (complet ou squelette) doit s'y conformer.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Ressource(BaseModel):
    """Lien externe : documentation officielle, article, tutoriel."""

    titre: str
    url: str


class Exercice(BaseModel):
    """Exercice tel que défini dans ``exercices.json``.

    Les champs texte (consigne, indices, solution) sont en Markdown,
    rendus en HTML par le moteur au moment de l'affichage.
    """

    id: str
    titre: str
    consigne: str
    indices: list[str] = Field(default_factory=list)
    ressources: list[Ressource] = Field(default_factory=list)
    solution: str = ""


class Projet(BaseModel):
    """Projet guidé de fin de chapitre (``projet.json``)."""

    titre: str
    consigne: str
    etapes: list[str] = Field(default_factory=list)
    indices: list[str] = Field(default_factory=list)
    ressources: list[Ressource] = Field(default_factory=list)
    solution: str = ""


class ChapitreMeta(BaseModel):
    """Métadonnées d'un chapitre (``chapitre.json``)."""

    numero: int
    titre: str
    description: str = ""
    objectifs: list[str] = Field(default_factory=list)
    points_theorie: list[str] = Field(default_factory=list)
    projets_cibles: list[str] = Field(default_factory=list)
    statut: Literal["complet", "squelette"] = "complet"


class Chapitre(BaseModel):
    """Chapitre assemblé depuis un dossier de ``app/content/``."""

    slug: str
    meta: ChapitreMeta
    theorie: str = ""  # Markdown brut ; rendu via le filtre Jinja `markdown`
    exercices: list[Exercice] = Field(default_factory=list)
    projet: Optional[Projet] = None


# ---------------------------------------------------------------------------
# Payloads de l'API de progression
# ---------------------------------------------------------------------------


class ExerciceProgress(BaseModel):
    chapitre: str
    exercice_id: str
    fait: bool


class ProjetProgress(BaseModel):
    chapitre: str
    fait: bool
