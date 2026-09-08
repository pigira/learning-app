"""Persistance SQLite de la progression utilisateur.

Deux tables : les exercices marqués « terminé » et les projets guidés
marqués « terminé ». Aucune donnée de contenu n'est stockée ici : la base
ne référence les cours/chapitres/exercices que par leurs identifiants.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

# Sur Azure App Service, le code déployé (wwwroot) est remplacé à chaque
# déploiement : la base ne doit pas vivre là. PROGRESS_DB_PATH permet de la
# rediriger vers le stockage persistant (/home) monté par App Service.
# En local, comportement inchangé : app/data/progress.db.
DB_PATH = Path(os.environ.get("PROGRESS_DB_PATH", DATA_DIR / "progress.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS exercice_progress (
    cours       TEXT NOT NULL,
    chapitre    TEXT NOT NULL,
    exercice_id TEXT NOT NULL,
    fait        INTEGER NOT NULL DEFAULT 0,
    maj_le      TEXT NOT NULL,
    PRIMARY KEY (cours, chapitre, exercice_id)
);

CREATE TABLE IF NOT EXISTS projet_progress (
    cours    TEXT NOT NULL,
    chapitre TEXT NOT NULL,
    fait     INTEGER NOT NULL DEFAULT 0,
    maj_le   TEXT NOT NULL,
    PRIMARY KEY (cours, chapitre)
);
"""


def _connexion() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _horodatage() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    """Crée le schéma et rattache atomiquement l'ancienne progression à Python."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _connexion()
    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            tables_a_migrer = []
            for table in ("exercice_progress", "projet_progress"):
                colonnes = {
                    ligne["name"]
                    for ligne in conn.execute(f"PRAGMA table_info({table})")
                }
                if colonnes and "cours" not in colonnes:
                    conn.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
                    tables_a_migrer.append(table)

            # executescript ferait un COMMIT implicite avant la copie des données.
            for instruction in _SCHEMA.split(";"):
                if instruction.strip():
                    conn.execute(instruction)

            for table in tables_a_migrer:
                colonnes = (
                    "chapitre, exercice_id, fait, maj_le"
                    if table == "exercice_progress"
                    else "chapitre, fait, maj_le"
                )
                conn.execute(
                    f"INSERT INTO {table} (cours, {colonnes}) "
                    f"SELECT 'python', {colonnes} FROM {table}_old"
                )
                conn.execute(f"DROP TABLE {table}_old")
    finally:
        conn.close()


def set_exercice_fait(cours: str, chapitre: str, exercice_id: str, fait: bool) -> None:
    conn = _connexion()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO exercice_progress (cours, chapitre, exercice_id, fait, maj_le)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (cours, chapitre, exercice_id)
                DO UPDATE SET fait = excluded.fait, maj_le = excluded.maj_le
                """,
                (cours, chapitre, exercice_id, int(fait), _horodatage()),
            )
    finally:
        conn.close()


def set_projet_fait(cours: str, chapitre: str, fait: bool) -> None:
    conn = _connexion()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO projet_progress (cours, chapitre, fait, maj_le)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (cours, chapitre)
                DO UPDATE SET fait = excluded.fait, maj_le = excluded.maj_le
                """,
                (cours, chapitre, int(fait), _horodatage()),
            )
    finally:
        conn.close()


def exercices_faits(cours: str, chapitre: str) -> set[str]:
    """Identifiants des exercices marqués terminés pour un chapitre."""
    conn = _connexion()
    try:
        lignes = conn.execute(
            "SELECT exercice_id FROM exercice_progress "
            "WHERE cours = ? AND chapitre = ? AND fait = 1",
            (cours, chapitre),
        ).fetchall()
    finally:
        conn.close()
    return {ligne["exercice_id"] for ligne in lignes}


def projet_fait(cours: str, chapitre: str) -> bool:
    conn = _connexion()
    try:
        ligne = conn.execute(
            "SELECT fait FROM projet_progress WHERE cours = ? AND chapitre = ?",
            (cours, chapitre),
        ).fetchone()
    finally:
        conn.close()
    return bool(ligne and ligne["fait"])


def tous_exercices_faits(cours: str) -> dict[str, set[str]]:
    """Pour un cours : chapitre -> ids des exercices terminés."""
    conn = _connexion()
    try:
        lignes = conn.execute(
            "SELECT chapitre, exercice_id FROM exercice_progress "
            "WHERE cours = ? AND fait = 1",
            (cours,),
        ).fetchall()
    finally:
        conn.close()
    resultat: dict[str, set[str]] = {}
    for ligne in lignes:
        resultat.setdefault(ligne["chapitre"], set()).add(ligne["exercice_id"])
    return resultat


def tous_projets_faits(cours: str) -> set[str]:
    conn = _connexion()
    try:
        lignes = conn.execute(
            "SELECT chapitre FROM projet_progress WHERE cours = ? AND fait = 1",
            (cours,),
        ).fetchall()
    finally:
        conn.close()
    return {ligne["chapitre"] for ligne in lignes}
