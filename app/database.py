"""Persistance SQLite de la progression utilisateur.

Deux tables : les exercices marqués « terminé » et les projets guidés
marqués « terminé ». Aucune donnée de contenu n'est stockée ici : la base
ne référence les chapitres/exercices que par leurs identifiants.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "progress.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS exercice_progress (
    chapitre    TEXT NOT NULL,
    exercice_id TEXT NOT NULL,
    fait        INTEGER NOT NULL DEFAULT 0,
    maj_le      TEXT NOT NULL,
    PRIMARY KEY (chapitre, exercice_id)
);

CREATE TABLE IF NOT EXISTS projet_progress (
    chapitre TEXT PRIMARY KEY,
    fait     INTEGER NOT NULL DEFAULT 0,
    maj_le   TEXT NOT NULL
);
"""


def _connexion() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _horodatage() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    """Crée le dossier de données et le schéma si nécessaire."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = _connexion()
    try:
        with conn:
            conn.executescript(_SCHEMA)
    finally:
        conn.close()


def set_exercice_fait(chapitre: str, exercice_id: str, fait: bool) -> None:
    conn = _connexion()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO exercice_progress (chapitre, exercice_id, fait, maj_le)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (chapitre, exercice_id)
                DO UPDATE SET fait = excluded.fait, maj_le = excluded.maj_le
                """,
                (chapitre, exercice_id, int(fait), _horodatage()),
            )
    finally:
        conn.close()


def set_projet_fait(chapitre: str, fait: bool) -> None:
    conn = _connexion()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO projet_progress (chapitre, fait, maj_le)
                VALUES (?, ?, ?)
                ON CONFLICT (chapitre)
                DO UPDATE SET fait = excluded.fait, maj_le = excluded.maj_le
                """,
                (chapitre, int(fait), _horodatage()),
            )
    finally:
        conn.close()


def exercices_faits(chapitre: str) -> set[str]:
    """Identifiants des exercices marqués terminés pour un chapitre."""
    conn = _connexion()
    try:
        lignes = conn.execute(
            "SELECT exercice_id FROM exercice_progress WHERE chapitre = ? AND fait = 1",
            (chapitre,),
        ).fetchall()
    finally:
        conn.close()
    return {ligne["exercice_id"] for ligne in lignes}


def projet_fait(chapitre: str) -> bool:
    conn = _connexion()
    try:
        ligne = conn.execute(
            "SELECT fait FROM projet_progress WHERE chapitre = ?", (chapitre,)
        ).fetchone()
    finally:
        conn.close()
    return bool(ligne and ligne["fait"])


def tous_exercices_faits() -> dict[str, set[str]]:
    """Pour la page d'accueil : chapitre -> ids des exercices terminés."""
    conn = _connexion()
    try:
        lignes = conn.execute(
            "SELECT chapitre, exercice_id FROM exercice_progress WHERE fait = 1"
        ).fetchall()
    finally:
        conn.close()
    resultat: dict[str, set[str]] = {}
    for ligne in lignes:
        resultat.setdefault(ligne["chapitre"], set()).add(ligne["exercice_id"])
    return resultat


def tous_projets_faits() -> set[str]:
    conn = _connexion()
    try:
        lignes = conn.execute(
            "SELECT chapitre FROM projet_progress WHERE fait = 1"
        ).fetchall()
    finally:
        conn.close()
    return {ligne["chapitre"] for ligne in lignes}
