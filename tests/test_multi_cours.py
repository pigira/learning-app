"""Regression tests: python -m unittest discover -s tests -v.

Only temporary content and databases are used; embedded course code is never run.
"""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from app import content, database, main


ANCIEN_SCHEMA = """
CREATE TABLE exercice_progress (
    chapitre TEXT NOT NULL,
    exercice_id TEXT NOT NULL,
    fait INTEGER NOT NULL DEFAULT 0,
    maj_le TEXT NOT NULL,
    PRIMARY KEY (chapitre, exercice_id)
);
CREATE TABLE projet_progress (
    chapitre TEXT PRIMARY KEY,
    fait INTEGER NOT NULL DEFAULT 0,
    maj_le TEXT NOT NULL
);
INSERT INTO exercice_progress VALUES ('chapitre_00_test', 'ex01', 1, 'date-ex01');
INSERT INTO exercice_progress VALUES ('chapitre_00_test', 'ex02', 0, 'date-ex02');
INSERT INTO projet_progress VALUES ('chapitre_00_test', 1, 'date-projet');
INSERT INTO projet_progress VALUES ('ancien_chapitre', 0, 'date-ancienne');
"""
SLUG = "chapitre_00_test"


class EnvironnementTemporaire(unittest.TestCase):
    def setUp(self):
        temporaire = tempfile.TemporaryDirectory()
        self.addCleanup(temporaire.cleanup)
        self.racine = Path(temporaire.name)
        self.contenu = self.racine / "content"
        self.contenu.mkdir()
        for cible, valeur in (
            ("app.content.CONTENT_DIR", self.contenu),
            ("app.database.DB_PATH", self.racine / "progress.db"),
        ):
            remplacement = patch(cible, valeur)
            remplacement.start()
            self.addCleanup(remplacement.stop)

    def ecrire_json(self, chemin, valeur):
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(valeur), encoding="utf-8")

    def creer_cours(self, slug="python", ordre=1, statut="disponible"):
        dossier = self.contenu / slug
        self.ecrire_json(
            dossier / "cours.json",
            {"ordre": ordre, "titre": slug, "statut": statut},
        )
        return dossier

    def creer_chapitre(self, cours="python", slug=SLUG, numero=0):
        dossier = self.contenu / cours / slug
        self.ecrire_json(
            dossier / "chapitre.json", {"numero": numero, "titre": slug}
        )
        self.ecrire_json(
            dossier / "exercices.json",
            [
                {"id": "ex01", "titre": "Premier", "consigne": "Consigne"},
                {"id": "ex02", "titre": "Second", "consigne": "Consigne"},
            ],
        )
        self.ecrire_json(
            dossier / "projet.json", {"titre": "Projet", "consigne": "Consigne"}
        )
        (dossier / "theorie.md").write_text("## Theorie\n\nContenu.", encoding="utf-8")
        return dossier

    def creer_ancienne_base(self):
        with closing(sqlite3.connect(database.DB_PATH)) as conn:
            conn.executescript(ANCIEN_SCHEMA)


class TestsContenu(EnvironnementTemporaire):
    def test_decouverte_tri_et_cours_a_venir_sans_chapitre(self):
        self.creer_cours("avenir", 3, "a_venir")
        self.creer_cours("autre", 2)
        self.creer_cours()
        self.creer_chapitre(slug="chapitre_02_test", numero=2)
        self.creer_chapitre()
        self.creer_chapitre("autre")
        self.creer_chapitre("sans_meta")

        cours, erreurs = content.charger_cours()

        self.assertEqual(erreurs, [])
        self.assertEqual([c.slug for c in cours], ["python", "autre", "avenir"])
        self.assertEqual([c.meta.numero for c in cours[0].chapitres], [0, 2])
        self.assertEqual(len(cours[1].chapitres), 1)
        self.assertEqual(cours[2].chapitres, [])
        self.assertIsNone(content.obtenir_cours_meta("sans_meta"))
        self.assertIsNone(content.obtenir_chapitre("sans_meta", SLUG))

    def test_erreurs_collectees_sans_bloquer_les_autres_contenus(self):
        self.creer_cours()
        self.creer_chapitre()
        invalide = self.creer_cours("invalide")
        (invalide / "cours.json").write_text("{", encoding="utf-8")
        mauvais_chapitre = self.creer_chapitre(slug="invalide")
        self.ecrire_json(mauvais_chapitre / "chapitre.json", {"numero": "non"})

        cours, erreurs = content.charger_cours()

        self.assertEqual([c.slug for c in cours], ["python"])
        self.assertEqual([c.slug for c in cours[0].chapitres], [SLUG])
        self.assertEqual(len(erreurs), 2)
        self.assertTrue(any("python/invalide" in e for e in erreurs))
        with self.assertRaises(content.ErreurContenu):
            content.obtenir_cours_meta("invalide")
        with self.assertRaises(content.ErreurContenu):
            content.obtenir_chapitre("python", "invalide")

    def test_schema_cours_et_valeurs_par_defaut(self):
        dossier = self.creer_cours()
        self.ecrire_json(dossier / "cours.json", {"ordre": 1, "titre": "Test"})
        meta = content.obtenir_cours_meta("python")
        self.assertEqual(meta.description, "")
        self.assertEqual(meta.statut, "disponible")
        self.assertTrue(meta.icone)
        valeurs_invalides = (
            [],
            {"titre": "Test"},
            {"ordre": 1, "titre": "Test", "statut": "autre"},
        )
        for valeur in valeurs_invalides:
            with self.subTest(valeur=valeur):
                self.ecrire_json(dossier / "cours.json", valeur)
                with self.assertRaises(content.ErreurContenu):
                    content.obtenir_cours_meta("python")

    def test_relecture_sans_cache_et_meta_sans_chapitres(self):
        dossier = self.creer_cours()
        self.creer_chapitre()
        with patch("app.content._charger_dossier", side_effect=AssertionError):
            self.assertEqual(content.obtenir_cours_meta("python").titre, "python")
        self.ecrire_json(dossier / "cours.json", {"ordre": 1, "titre": "Nouveau"})
        self.assertEqual(content.charger_cours()[0][0].meta.titre, "Nouveau")
        self.creer_cours("ajout", 2)
        self.assertEqual(len(content.charger_cours()[0]), 2)

    def test_traversees_chemins_absolus_et_liens_symboliques(self):
        self.creer_cours()
        self.creer_chapitre()
        self.creer_cours("autre")
        self.creer_chapitre("autre")
        for slug in ("", ".", "..", "../content/python", str(self.contenu / "python")):
            with self.subTest(cours=slug):
                self.assertIsNone(content.obtenir_cours_meta(slug))
                self.assertIsNone(content.obtenir_chapitre(slug, SLUG))
                self.assertTrue(content.charger_chapitres(slug)[1])
        slugs_invalides = (
            "", ".", "..", f"../autre/{SLUG}", str(self.contenu / "autre" / SLUG)
        )
        for slug in slugs_invalides:
            with self.subTest(chapitre=slug):
                self.assertIsNone(content.obtenir_chapitre("python", slug))
        exterieur = self.racine / "exterieur"
        self.ecrire_json(exterieur / "cours.json", {"ordre": 1, "titre": "Exterieur"})
        (self.contenu / "lien").symlink_to(exterieur, target_is_directory=True)
        (self.contenu / "python" / "lien").symlink_to(
            self.contenu / "autre" / SLUG, target_is_directory=True
        )
        self.assertIsNone(content.obtenir_cours_meta("lien"))
        self.assertIsNone(content.obtenir_chapitre("python", "lien"))
        cours, erreurs = content.charger_cours()
        self.assertEqual(len(cours), 2)
        self.assertEqual(len(erreurs), 2)


class TestsBase(EnvironnementTemporaire):
    def test_creation_et_isolation_des_six_fonctions(self):
        database.init_db()
        for cours in ("python", "autre"):
            database.set_exercice_fait(cours, SLUG, "ex01", True)
            database.set_projet_fait(cours, SLUG, True)
        database.set_exercice_fait("autre", SLUG, "ex01", False)
        database.set_projet_fait("autre", SLUG, False)
        database.init_db()

        self.assertEqual(database.exercices_faits("python", SLUG), {"ex01"})
        self.assertEqual(database.exercices_faits("autre", SLUG), set())
        self.assertTrue(database.projet_fait("python", SLUG))
        self.assertFalse(database.projet_fait("autre", SLUG))
        self.assertEqual(database.tous_exercices_faits("python"), {SLUG: {"ex01"}})
        self.assertEqual(database.tous_exercices_faits("autre"), {})
        self.assertEqual(database.tous_projets_faits("python"), {SLUG})
        self.assertEqual(database.tous_projets_faits("autre"), set())

    def test_migration_preserve_toutes_les_valeurs_et_est_idempotente(self):
        self.creer_ancienne_base()
        with closing(sqlite3.connect(database.DB_PATH)) as conn:
            avant = {
                table: conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
                for table in ("exercice_progress", "projet_progress")
            }
        database.init_db()
        database.init_db()
        with closing(sqlite3.connect(database.DB_PATH)) as conn:
            for table, lignes in avant.items():
                apres = conn.execute(f"SELECT * FROM {table} ORDER BY 2, 3").fetchall()
                self.assertEqual(apres, [("python",) + ligne for ligne in lignes])
                colonnes = conn.execute(f"PRAGMA table_info({table})").fetchall()
                cle = [c[1] for c in sorted(colonnes, key=lambda c: c[5]) if c[5]]
                attendue = ["cours", "chapitre"]
                if table == "exercice_progress":
                    attendue.append("exercice_id")
                self.assertEqual(cle, attendue)
            self.assertEqual(
                conn.execute(
                    "SELECT name FROM sqlite_master WHERE name LIKE '%_old'"
                ).fetchall(),
                [],
            )

    def test_echec_de_copie_annule_aussi_les_modifications_de_schema(self):
        self.creer_ancienne_base()
        schema_echec = database._SCHEMA.replace(
            "PRIMARY KEY (cours, chapitre)",
            "CHECK (cours <> 'python'), PRIMARY KEY (cours, chapitre)",
        )
        with patch("app.database._SCHEMA", schema_echec):
            with self.assertRaises(sqlite3.IntegrityError):
                database.init_db()
        with closing(sqlite3.connect(database.DB_PATH)) as conn:
            for table in ("exercice_progress", "projet_progress"):
                colonnes = conn.execute(f"PRAGMA table_info({table})").fetchall()
                self.assertNotIn("cours", [c[1] for c in colonnes])
                total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                self.assertEqual(total, 2)
            self.assertEqual(
                conn.execute(
                    "SELECT name FROM sqlite_master WHERE name LIKE '%_old'"
                ).fetchall(),
                [],
            )
        database.init_db()
        self.assertEqual(database.exercices_faits("python", SLUG), {"ex01"})

    def test_migration_avec_une_seule_table_existante(self):
        self.creer_ancienne_base()
        with closing(sqlite3.connect(database.DB_PATH)) as conn:
            conn.execute("DROP TABLE projet_progress")
        database.init_db()
        self.assertEqual(database.exercices_faits("python", SLUG), {"ex01"})
        self.assertEqual(database.tous_projets_faits("python"), set())


class TestsRoutes(EnvironnementTemporaire, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.creer_cours()
        self.creer_chapitre()
        self.creer_cours("autre", 2)
        self.creer_chapitre("autre")
        self.creer_cours("avenir", 3, "a_venir")
        database.init_db()

    async def requete(self, chemin, payload=None):
        """Exercise the real ASGI router without an extra HTTP client dependency."""
        messages = []
        corps = json.dumps(payload).encode() if payload is not None else b""
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST" if payload is not None else "GET",
            "scheme": "http",
            "path": chemin,
            "raw_path": chemin.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [(b"host", b"testserver"), (b"content-type", b"application/json")],
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
        }

        async def recevoir():
            return {"type": "http.request", "body": corps, "more_body": False}

        async def envoyer(message):
            messages.append(message)

        await main.app(scope, recevoir, envoyer)
        statut = next(m["status"] for m in messages if m["type"] == "http.response.start")
        texte = b"".join(m.get("body", b"") for m in messages).decode()
        return statut, texte

    async def test_hub_navigation_et_cartes_non_cliquables(self):
        statut, hub = await self.requete("/")
        self.assertEqual(statut, 200)
        self.assertIn('href="/cours/python"', hub)
        self.assertNotIn('href="/cours/avenir"', hub)
        self.assertIn('<article class="carte carte-cours carte-a-venir">', hub)
        self.assertNotIn("chapitres termin", hub)
        statut, cours = await self.requete("/cours/python")
        self.assertEqual(statut, 200)
        self.assertIn(f'href="/cours/python/chapitre/{SLUG}"', cours)
        statut, chapitre = await self.requete(f"/cours/python/chapitre/{SLUG}")
        self.assertEqual(statut, 200)
        self.assertIn('data-cours="python"', chapitre)
        self.assertIn(f'data-chapitre="{SLUG}"', chapitre)
        self.assertIn('href="/"', chapitre)
        self.assertIn('href="/cours/python"', chapitre)
        self.assertIn('<div id="projet-contenu" class="cache">', chapitre)
        self.assertEqual((await self.requete("/cours/avenir"))[0], 200)

    async def test_coches_persistantes_deverrouillage_et_resume_isoles(self):
        payload = {"cours": "python", "chapitre": SLUG, "fait": True}
        for exercice_id in ("ex01", "ex02"):
            statut, reponse = await self.requete(
                "/api/progress/exercice", {**payload, "exercice_id": exercice_id}
            )
            self.assertEqual(statut, 200)
        self.assertEqual(
            json.loads(reponse),
            {"ok": True, "faits": 2, "total": 2, "tous_faits": True},
        )
        self.assertIn("0/1 chapitres termin", (await self.requete("/"))[1])
        self.assertEqual((await self.requete("/api/progress/projet", payload))[0], 200)
        database.init_db()
        _, chapitre = await self.requete(f"/cours/python/chapitre/{SLUG}")
        self.assertIn('<div id="projet-contenu" class="">', chapitre)
        self.assertEqual(chapitre.count("checked"), 3)
        _, autre = await self.requete(f"/cours/autre/chapitre/{SLUG}")
        self.assertNotIn("checked", autre)
        _, hub = await self.requete("/")
        self.assertEqual(hub.count("chapitres termin"), 1)
        self.assertIn("1/1 chapitres termin", hub)
        await self.requete(
            "/api/progress/exercice",
            {**payload, "exercice_id": "ex02", "fait": False},
        )
        await self.requete("/api/progress/projet", {**payload, "fait": False})
        self.assertEqual(database.exercices_faits("python", SLUG), {"ex01"})
        self.assertFalse(database.projet_fait("python", SLUG))

    async def test_entrees_orphelines_ignorees(self):
        database.set_exercice_fait("python", SLUG, "supprime", True)
        database.set_exercice_fait("python", "supprime", "ex01", True)
        database.set_projet_fait("python", "supprime", True)
        self.assertNotIn("chapitres termin", (await self.requete("/"))[1])
        for exercice_id in ("ex01", "ex02"):
            database.set_exercice_fait("python", SLUG, exercice_id, True)
        database.set_projet_fait("python", SLUG, True)
        self.assertIn("1/1 chapitres termin", (await self.requete("/"))[1])

    async def test_erreurs_http_sans_ecriture_de_progression(self):
        chemins_inconnus = (
            "/cours/inconnu",
            f"/cours/inconnu/chapitre/{SLUG}",
            "/cours/python/chapitre/inconnu",
        )
        for chemin in chemins_inconnus:
            self.assertEqual((await self.requete(chemin))[0], 404)
        for endpoint in ("/api/progress/exercice", "/api/progress/projet"):
            payload = {"chapitre": SLUG, "exercice_id": "ex01", "fait": True}
            self.assertEqual((await self.requete(endpoint, payload))[0], 422)
            for cours in ("inconnu", "..", "../content/python", "avenir"):
                reponse = await self.requete(endpoint, {**payload, "cours": cours})
                self.assertEqual(reponse[0], 404)
            reponse = await self.requete(
                endpoint,
                {**payload, "cours": "python", "chapitre": "../autre/" + SLUG},
            )
            self.assertEqual(reponse[0], 404)
        payload = {"cours": "python", "chapitre": SLUG, "fait": True}
        reponse = await self.requete(
            "/api/progress/exercice", {**payload, "exercice_id": "inconnu"}
        )
        self.assertEqual(reponse[0], 404)
        (self.contenu / "python" / SLUG / "projet.json").unlink()
        self.assertEqual(
            (await self.requete("/api/progress/projet", payload))[0],
            404,
        )
        self.assertEqual(database.tous_exercices_faits("python"), {})
        self.assertEqual(database.tous_projets_faits("python"), set())

    async def test_contenu_invalide_signale_et_meta_independante(self):
        dossier = self.contenu / "python"
        (dossier / SLUG / "chapitre.json").write_text("{", encoding="utf-8")
        self.assertEqual((await self.requete("/"))[0], 200)
        self.assertEqual((await self.requete("/cours/python"))[0], 200)
        self.assertEqual((await self.requete(f"/cours/python/chapitre/{SLUG}"))[0], 500)
        (dossier / "cours.json").write_text("{", encoding="utf-8")
        statut, hub = await self.requete("/")
        self.assertEqual(statut, 200)
        self.assertIn("JSON invalide", hub)
        self.assertIn('href="/cours/autre"', hub)
        self.assertEqual((await self.requete("/cours/python"))[0], 500)


if __name__ == "__main__":
    unittest.main()
