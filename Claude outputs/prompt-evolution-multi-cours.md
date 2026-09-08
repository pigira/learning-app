# Prompt — Évolution V2 : hub multi-cours

## Contexte

Tu interviens sur cette application locale d'apprentissage (FastAPI + SQLite +
contenu Markdown/JSON), actuellement mono-cours (« Apprendre Python »,
22 chapitres). Lis `README.md`, `app/main.py`, `app/content.py`,
`app/models.py`, `app/database.py` et un chapitre existant
(`app/content/chapitre_01_fondamentaux/`) avant de commencer : le moteur
actuel est agnostique du **contenu** d'un chapitre, mais suppose un seul
cours implicite (racine `app/content/` = liste de chapitres).

## Objectif

Transformer l'app en **hub multi-cours** : page d'accueil listant les cours
disponibles (et à venir), sélection d'un cours, puis parcours chapitre par
chapitre identique à l'existant. Premier cours = l'actuel « Python »
(déplacé, contenu inchangé). D'autres cours (ex. microcontrôleurs/ESP32,
Fusion 360, impression 3D) seront rédigés plus tard par l'agent rédacteur —
cette évolution ne doit **pas** générer leur contenu, seulement rendre le
moteur capable de les accueillir sans modification de code future, exactement
comme l'ajout d'un chapitre aujourd'hui.

Objectif implicite : garder la philosophie actuelle intacte — zéro build
front, contenu relu à chaque requête, ajouter un cours = ajouter un dossier.

## 1. Nouvelle arborescence de contenu

```
app/content/
├── python/
│   ├── cours.json                        # nouveau
│   ├── chapitre_00_setup_environnement/  # déplacés tels quels
│   ├── chapitre_01_fondamentaux/
│   ├── ...
│   └── chapitre_21_projet_final/
├── esp32-microcontroleurs/               # exemple de cours « à venir »
│   └── cours.json
└── impression-3d-fusion360/              # autre exemple placeholder
    └── cours.json
```

Déplace les 22 dossiers `chapitre_XX_*` actuels dans `app/content/python/`
via `git mv` (préserve l'historique). Crée `app/content/python/cours.json` :

```json
{
  "ordre": 1,
  "titre": "Apprendre Python",
  "description": "Du setup macOS au déploiement Docker avec IA.",
  "icone": "🐍",
  "statut": "disponible"
}
```

Crée 1 à 2 dossiers cours placeholder (`statut: "a_venir"`, pas de
sous-dossier chapitre) pour valider le rendu du hub avec du contenu à venir,
par exemple :

```json
{
  "ordre": 2,
  "titre": "Microcontrôleurs & ESP32",
  "description": "Firmware, capteurs, communication sans fil.",
  "icone": "🔌",
  "statut": "a_venir"
}
```

Slugs de dossier = clé du cours (comme le slug de chapitre aujourd'hui) :
pas de champ `slug` dans `cours.json`, dérivé du nom de dossier — même
convention que `chapitre.json`.

## 2. Modèles (`app/models.py`)

Ajoute, sans toucher aux modèles existants (`Chapitre`, `ChapitreMeta`,
`Exercice`, `Projet` restent identiques — schéma des JSON de chapitre
inchangé) :

```python
class CoursMeta(BaseModel):
    """Métadonnées d'un cours (``cours.json``)."""

    ordre: int
    titre: str
    description: str = ""
    icone: str = "📚"
    statut: Literal["disponible", "a_venir"] = "disponible"


class Cours(BaseModel):
    """Cours assemblé depuis un dossier de ``app/content/``."""

    slug: str
    meta: CoursMeta
    chapitres: list[Chapitre] = Field(default_factory=list)
```

## 3. Découverte de contenu (`app/content.py`)

Restructure autour de deux niveaux, en réutilisant la logique actuelle de
chargement de chapitre telle quelle (elle ne change pas), simplement portée
sur un sous-dossier de cours :

- `charger_cours() -> tuple[list[Cours], list[str]]` : itère les
  sous-dossiers de `CONTENT_DIR` contenant un `cours.json`, charge leurs
  métadonnées + leurs chapitres (réutilise la boucle existante de
  `charger_chapitres`, scopée à `CONTENT_DIR / cours_slug`), trie par
  `meta.ordre`. Dossiers invalides → erreurs collectées, comme aujourd'hui
  pour les chapitres.
- `obtenir_cours_meta(cours_slug) -> Optional[CoursMeta]` : lecture seule du
  `cours.json`, sans charger les chapitres (utile pour le fil d'ariane de la
  page chapitre, évite de tout recharger juste pour un titre).
- `charger_chapitres(cours_slug) -> tuple[list[Chapitre], list[str]]` :
  identique à l'actuelle mais scopée à `CONTENT_DIR / cours_slug` au lieu de
  `CONTENT_DIR`.
- `obtenir_chapitre(cours_slug, slug) -> Optional[Chapitre]` : ajoute
  `cours_slug`. Garde-fou anti-traversée : le dossier résolu doit être un
  enfant direct de `CONTENT_DIR / cours_slug`, pas de `CONTENT_DIR` seul.

Garde le même garde-fou anti-traversée pour `cours_slug` lui-même (enfant
direct de `CONTENT_DIR`).

## 4. Base de données (`app/database.py`)

Le slug de chapitre n'est plus unique globalement (deux cours peuvent avoir
un `chapitre_00_...`) : `cours` doit faire partie de la clé primaire des
deux tables.

```sql
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
```

Ajoute `cours: str` en premier paramètre de toutes les fonctions existantes
(`set_exercice_fait`, `set_projet_fait`, `exercices_faits`, `projet_fait`,
`tous_exercices_faits`, `tous_projets_faits`) — ces deux dernières
deviennent scopées à un cours (`tous_exercices_faits(cours)`,
`tous_projets_faits(cours)`).

**Migration automatique et silencieuse dans `init_db()`** — la base
existante de Pierre contient déjà de la progression sur les chapitres
Python, elle ne doit pas être perdue : avant `executescript(_SCHEMA)`,
détecte l'ancien schéma (`PRAGMA table_info(exercice_progress)` sans colonne
`cours`) et, si présent, migre en une transaction :

1. `ALTER TABLE exercice_progress RENAME TO exercice_progress_old` (idem
   `projet_progress`).
2. Crée les nouvelles tables (nouveau schéma).
3. `INSERT INTO exercice_progress (cours, chapitre, exercice_id, fait, maj_le)
   SELECT 'python', chapitre, exercice_id, fait, maj_le FROM
   exercice_progress_old` (idem projet).
4. `DROP TABLE exercice_progress_old` (idem projet).

Idempotent : si les tables n'existent pas encore (première installation) ou
ont déjà `cours`, ne fait rien de spécial — `CREATE TABLE IF NOT EXISTS`
suffit.

## 5. Routes (`app/main.py`)

- `GET /` → **hub** : `content.charger_cours()`, agrège la progression par
  cours (boucle sur les cours disponibles, réutilise
  `database.tous_exercices_faits(cours.slug)` /
  `tous_projets_faits(cours.slug)` + la logique `_statut_chapitre` existante
  pour un résumé global par cours), rend `hub.html`.
- `GET /cours/{cours_slug}` → reprend telle quelle la logique actuelle de
  `index()` (liste de cartes chapitres + statuts), scopée au cours, rend
  `cours.html` (renommage de l'actuel `index.html`). 404 si `cours_slug`
  inconnu ou `cours.json` absent.
- `GET /cours/{cours_slug}/chapitre/{slug}` → reprend `page_chapitre()`
  telle quelle, ajoute `cours_slug` aux appels `content.obtenir_chapitre` et
  aux fonctions `database`, passe `cours_meta` (via `obtenir_cours_meta`) au
  template pour le fil d'ariane.
- `POST /api/progress/exercice` et `/api/progress/projet` → ajoute
  `cours: str` aux modèles Pydantic `ExerciceProgress`/`ProjetProgress` et
  répercute-le dans les appels `database.*` et la vérification d'existence
  du chapitre (`content.obtenir_chapitre(cours, chapitre)`).

Renomme le titre FastAPI (`FastAPI(title="Hub Apprentissage", ...)`) —
simple constante, pas de conséquence fonctionnelle.

## 6. Templates

- **`hub.html`** (nouveau, remplace `index.html` comme page de `/`) : une
  carte par cours (icône, titre, description, badge `disponible` /
  `bientôt disponible`), lien vers `/cours/{slug}` seulement si
  `disponible` — sinon carte non cliquable, style atténué (réutilise le
  pattern `.badge-squelette` → ajoute `.badge-a-venir` dans `style.css`). Si
  un cours `disponible` a une progression, affiche un résumé (`X/Y
  chapitres terminés`), sinon juste sa description.
- **`cours.html`** (renommage de `index.html`) : contenu inchangé, ajoute
  juste `<nav class="fil-ariane"><a href="/">&larr; Hub</a></nav>` en haut,
  comme `chapitre.html` le fait déjà pour son propre niveau.
- **`chapitre.html`** : fil d'ariane devient
  `Hub → {{ cours_meta.titre }} → chapitre courant` (deux liens : `/` et
  `/cours/{{ cours_slug }}`). `data-chapitre` sur `<body>` reste, ajoute
  `data-cours="{{ cours_slug }}"`.
- **`base.html`** : `brand`/sous-titre redeviennent génériques (`Hub
  Apprentissage`), plus de mention « Python » en dur.

## 7. `app/static/app.js`

Les appels `fetch` vers `/api/progress/exercice` et `/api/progress/projet`
doivent inclure `cours` dans le payload JSON — lis-le depuis
`document.body.dataset.cours` (nouvel attribut posé par `chapitre.html`),
exactement comme `slug` est lu aujourd'hui depuis `dataset.chapitre`.

## 8. Impacts connexes à corriger (mécaniques, pas de refonte)

- `agents/validate_chapter.py` importe `content.obtenir_chapitre(slug)` :
  signature à mettre à jour (`obtenir_chapitre(cours, slug)`), CLI à
  adapter (`python -m agents.validate_chapter <cours>/<slug>` ou deux
  arguments positionnels — à toi de choisir, documente le choix dans le
  script).
- **Hors périmètre de ce prompt**, à signaler dans ton compte rendu sans le
  traiter : `agents/redacteur-chapitre.source.md` et les skills
  `theorie`/`exercice`/`projet` supposent un seul cours et un `numero` de
  chapitre unique dans tout le dépôt — ils devront être adaptés (chemin
  `app/content/<cours>/...`, unicité de `numero` par cours et non globale)
  avant de rédiger le prochain cours. Ne les modifie pas maintenant.

## 9. Documentation

Mets à jour `README.md` : arborescence (`Structure du projet`), section
`Ajouter ou compléter un chapitre` (préciser le niveau cours), et ajoute une
section `Ajouter un cours` symétrique (créer `app/content/<slug>/cours.json`,
statut `a_venir` tant qu'aucun chapitre n'existe). Le tableau `## État du
contenu` reste sous `python/` sans changement de contenu, juste de chemin.

## 10. Style / conventions à respecter

- Le moteur (`main.py`, `content.py`, `database.py`, `models.py`) est écrit
  en **français** — noms de fonctions/variables, docstrings
  (`charger_chapitres`, `obtenir_chapitre`, `ErreurContenu`...). Garde cette
  convention pour tout le nouveau code du moteur. La règle « anglais pour le
  code » des instructions du projet concerne le code Python **pédagogique**
  à l'intérieur des exercices, pas le moteur lui-même.
- Zéro dépendance front nouvelle, zéro build : CSS/JS vanilla comme
  aujourd'hui.
- Le contenu reste relu à chaque requête (pas de cache) — cohérent avec
  l'échelle (quelques cours, quelques dizaines de chapitres).
- Ne touche pas au schéma de `chapitre.json` / `exercices.json` /
  `projet.json` ni à leur logique de chargement/validation existante
  (`_charger_dossier`) : seule la racine de recherche change.

## Definition of done

- [ ] `/` affiche le hub avec la carte Python (disponible, avec
      progression) et au moins une carte « à venir ».
- [ ] `/cours/python` affiche les 22 chapitres, comportement identique à
      l'actuel `/`.
- [ ] `/cours/python/chapitre/chapitre_01_fondamentaux` fonctionne, cases à
      cocher persistées.
- [ ] Une progression déjà cochée avant la migration (vérifier sur
      `app/data/progress.db` actuelle) est toujours visible après démarrage
      sur le nouveau schéma.
- [ ] `python -m agents.validate_chapter ...` fonctionne avec la nouvelle
      signature sur au moins un chapitre Python.
- [ ] README à jour.
- [ ] Cours « à venir » non cliquable, sans lien mort, sans erreur si son
      dossier n'a aucun sous-dossier chapitre.
