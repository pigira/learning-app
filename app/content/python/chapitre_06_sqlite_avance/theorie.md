Le JSON du chapitre 5 suffit pour une sauvegarde ; il s'effondre dès qu'il faut chercher, croiser, agréger. SQLite — une base relationnelle complète dans un simple fichier, incluse dans Python — est la persistance de tes trois projets. Ce chapitre couvre le module `sqlite3`, la modélisation relationnelle, les jointures, les transactions et les migrations.

## 1. Le module `sqlite3`

```python
import sqlite3

conn = sqlite3.connect("data/enduro.db")     # crée le fichier si absent
conn.row_factory = sqlite3.Row               # lignes accessibles par nom de colonne
conn.execute("PRAGMA foreign_keys = ON")     # OBLIGATOIRE (voir §3)

lignes = conn.execute(
    "SELECT date, duree_min FROM seances WHERE sport = ?",
    ("course",),                             # paramètre → tuple, même seul
).fetchall()

for ligne in lignes:
    print(ligne["date"], ligne["duree_min"])

conn.close()
```

Points clés :

- `row_factory = sqlite3.Row` : sans lui, les lignes sont des tuples anonymes (`ligne[1]` — illisible).
- **Requêtes paramétrées, toujours.** Le `?` est remplacé par le driver, avec échappement correct. Un SQL construit en f-string (`f"... WHERE sport = '{sport}'"`) est une **injection SQL** en puissance : `sport = "'; DROP TABLE seances; --"` et ta base disparaît. Règle absolue, détaillée au chapitre 19 : les valeurs passent par `?`, jamais par le texte de la requête.
- `executemany` insère un lot efficacement :

```python
conn.executemany(
    "INSERT INTO seances (date, sport, duree_min) VALUES (?, ?, ?)",
    [("2026-06-01", "course", 48), ("2026-06-03", "velo", 95)],
)
```

## 2. Modéliser : tables et relations

Le passage `list[dict]` → relationnel se joue sur les **relations** :

- **1-N** (une séance a plusieurs laps) : la table « enfant » porte une clé étrangère vers le parent.
- **N-N** (une recette a plusieurs ingrédients, un ingrédient sert dans plusieurs recettes) : une **table de liaison** porte les deux clés étrangères (+ les attributs de la relation, comme la quantité).

```sql
CREATE TABLE seances (
    id        INTEGER PRIMARY KEY,           -- auto-incrémenté en SQLite
    date      TEXT NOT NULL,                 -- ISO "2026-07-06" (tri correct)
    sport     TEXT NOT NULL,
    duree_min INTEGER NOT NULL CHECK (duree_min > 0)
);

CREATE TABLE laps (
    id         INTEGER PRIMARY KEY,
    seance_id  INTEGER NOT NULL REFERENCES seances(id) ON DELETE CASCADE,
    numero     INTEGER NOT NULL,
    duree_s    INTEGER NOT NULL,
    fc_moy     INTEGER,                      -- NULL si pas de capteur
    UNIQUE (seance_id, numero)
);
```

Choix à retenir : dates en TEXT ISO ; `NOT NULL` par défaut, NULL seulement quand l'absence a un sens (capteur manquant) ; `CHECK` pour les invariants simples ; `UNIQUE` pour ce qui ne doit pas exister en double ; `ON DELETE CASCADE` pour que les enfants suivent le parent.

SQLite ne vérifie les clés étrangères **que si** `PRAGMA foreign_keys = ON` est exécuté sur chaque connexion — piège historique n°1 : sans lui, un `laps.seance_id` orphelin s'insère sans erreur.

## 3. Jointures et agrégats

```sql
-- Les laps d'une séance (1-N) :
SELECT s.date, l.numero, l.duree_s
FROM laps AS l
JOIN seances AS s ON s.id = l.seance_id
WHERE s.date = '2026-06-01';

-- N-N : quelles recettes utilisent du parmesan ?
SELECT r.nom
FROM recettes AS r
JOIN recette_ingredients AS ri ON ri.recette_id = r.id
JOIN ingredients AS i ON i.id = ri.ingredient_id
WHERE i.nom = 'parmesan';

-- Agrégats : volume hebdomadaire par sport
SELECT strftime('%Y-W%W', date) AS semaine, sport,
       SUM(duree_min) AS total_min, COUNT(*) AS nb
FROM seances
GROUP BY semaine, sport
ORDER BY semaine;
```

- `JOIN` (INNER) ne garde que les correspondances ; `LEFT JOIN` garde toutes les lignes de gauche (les manquantes à droite deviennent NULL) — indispensable pour « les recettes **sans** ingrédient X » ou « les séances sans laps ».
- `GROUP BY` + `SUM/COUNT/AVG/MIN/MAX` : c'est l'idiome d'accumulation du chapitre 2, exécuté par le moteur. `HAVING` filtre après agrégation (`HAVING total_min > 300`).

## 4. Index et performance

Un index accélère les recherches sur une colonne au prix d'un léger surcoût à l'écriture :

```sql
CREATE INDEX idx_seances_date ON seances(date);
CREATE UNIQUE INDEX idx_cours_ticker_date ON cours(ticker, date);
```

Diagnostic : préfixer la requête par `EXPLAIN QUERY PLAN` — `SCAN seances` = parcours complet, `SEARCH seances USING INDEX ...` = index utilisé. Règle pratique : indexer les colonnes des `WHERE`/`JOIN` fréquents, et laisser `UNIQUE` créer les index d'unicité. Sur quelques milliers de lignes tout est instantané ; l'écart se voit à partir de ~10⁵ lignes (l'exercice 4 le mesure).

## 5. Transactions

Une transaction rend un groupe d'écritures **atomique** : tout ou rien — la version base de données de l'écriture atomique du chapitre 5.

```python
try:
    with conn:                       # BEGIN ... COMMIT, ou ROLLBACK si exception
        conn.execute("INSERT INTO seances ...", ...)
        conn.executemany("INSERT INTO laps ...", laps)
except sqlite3.IntegrityError as exc:
    print(f"import annulé, base intacte : {exc}")
```

`with conn:` commite en sortie normale et **rollback** si le bloc lève. Attention à la nuance : ce `with` ne ferme pas la connexion (contrairement au `with open`), il gère la transaction — d'où le `finally: conn.close()` de `database.py` de cette application.

Corollaire indispensable, l'**upsert** (insérer ou mettre à jour, rejouable sans doublon) :

```sql
INSERT INTO cours (ticker, date, valeur) VALUES (?, ?, ?)
ON CONFLICT (ticker, date) DO UPDATE SET valeur = excluded.valeur;
```

C'est la clé de l'**idempotence** : un import relancé deux fois ne crée rien en double (les jobs planifiés du chapitre 15 en dépendent).

## 6. Migrations avec Alembic

Ta base vit : ajouter une colonne `ressenti`, un index, une table... Modifier le schéma à la main sur une base qui contient des données = pertes assurées un jour. Une **migration** est un script versionné qui fait évoluer le schéma, avec marche arrière.

[Alembic](https://alembic.sqlalchemy.org) est l'outil standard (il s'appuie sur SQLAlchemy pour se connecter, même si ton code applicatif reste en `sqlite3` pur) :

```bash
pip install alembic
alembic init migrations                 # arborescence + alembic.ini
# dans alembic.ini : sqlalchemy.url = sqlite:///data/enduro.db
alembic revision -m "ajout colonne ressenti"
```

Le script généré se complète à la main :

```python
def upgrade():
    op.add_column("seances", sa.Column("ressenti", sa.Integer))
    op.create_index("idx_seances_date", "seances", ["date"])

def downgrade():
    op.drop_index("idx_seances_date")
    op.drop_column("seances", "ressenti")
```

```bash
alembic upgrade head        # applique tout ce qui manque
alembic downgrade -1        # marche arrière d'un cran
```

Alembic tient une table `alembic_version` dans ta base : il sait où chaque base en est. Le réflexe : **toute** modification de schéma passe par une révision, dès maintenant — c'est indolore au début et vital quand la base contient six mois de séances.

## 7. Organisation du code

Regroupe l'accès aux données dans un module `db.py` : connexion (PRAGMA compris), `init_db()` idempotente (`CREATE TABLE IF NOT EXISTS`), et une fonction par requête métier — le reste de l'application ne voit jamais de SQL. C'est exactement la structure de `app/database.py` de cette application, à relire avec l'œil de ce chapitre.

## Checklist de fin de chapitre

- [ ] `row_factory`, PRAGMA foreign_keys, requêtes paramétrées `?` : mes trois réflexes de connexion.
- [ ] Je modélise 1-N (clé étrangère) et N-N (table de liaison) avec NOT NULL/CHECK/UNIQUE/CASCADE réfléchis.
- [ ] J'écris jointures (INNER/LEFT) et agrégats GROUP BY sans chercher la syntaxe.
- [ ] Je sais lire EXPLAIN QUERY PLAN et poser un index utile.
- [ ] Toute écriture multiple passe par une transaction ; mes imports sont des upserts idempotents.
- [ ] Mon schéma évolue par migrations Alembic, jamais à la main.
