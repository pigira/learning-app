# Apprendre Python — application locale d'apprentissage

Application web locale (FastAPI + SQLite) structurée en 22 chapitres progressifs : théorie courte, exercices avec indices progressifs / ressources / correction commentée, et projet guidé de fin de chapitre. Du setup macOS au déploiement Docker avec intégration IA.

Le moteur est **totalement agnostique du contenu** : les chapitres vivent en fichiers Markdown + JSON dans `app/content/`. Ajouter ou modifier un chapitre ne demande aucune modification de code — ni même de redémarrage du serveur (le contenu est relu à chaque requête).

## Installation (macOS)

Prérequis : Python ≥ 3.10 (3.12 recommandé, `brew install python@3.12`).

```bash
cd "chemin/vers/Application de learning"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```bash
uvicorn app.main:app --reload
```

Puis ouvrir <http://127.0.0.1:8000>. `--reload` relance le serveur si le code Python change (inutile pour le contenu, qui est relu à chaud).

## Utilisation

- **Accueil** : liste des chapitres avec statut (non commencé / en cours / terminé) et progression.
- **Page chapitre** : théorie en haut, puis exercices — chaque exercice propose des boutons *Indice 1/2/3* (révélés un par un), *Ressources* (liens externes) et *Voir la correction*.
- La progression se coche manuellement (checkbox « Terminé ») et est persistée dans `app/data/progress.db` (SQLite). Aucune vérification automatique du code : tu testes dans VS Code, tu coches quand c'est fait.
- Le **projet guidé** de fin de chapitre se déverrouille quand tous les exercices du chapitre sont cochés.
- Réinitialiser la progression : supprimer `app/data/progress.db` (recréée au démarrage).

## État du contenu

**Les 22 chapitres (0 à 21) sont complets** : chacun a une théorie rédigée (`theorie.md`), 4 à 6 exercices détaillés (consigne + indices progressifs + ressources + correction commentée) et un projet guidé de fin de chapitre. Soit **104 exercices** au total.

| # | Chapitre | Ex. | Projet(s) cible |
|---|---|---|---|
| 0 | Setup de l'environnement (macOS) | 6 | Tous |
| 1 | Fondamentaux Python | 6 | Tous |
| 2 | Structures de données | 6 | Tous |
| 3 | POO en Python | 6 | Tous |
| 4 | Modules, exceptions et typing | 5 | Tous |
| 5 | Fichiers, JSON et context managers | 5 | Tous |
| 6 | SQLite avancé | 5 | Cuisine, Finance, Enduro |
| 7 | Tests et qualité de code | 5 | Tous |
| 8 | Async Python | 5 | Cuisine, Finance |
| 9 | Consommation d'API REST | 5 | Cuisine, Finance |
| 10 | Pandas | 5 | Finance, Enduro |
| 11 | Séries temporelles avec Pandas | 5 | Finance, Enduro |
| 12 | Visualisation de données | 4 | Finance, Enduro |
| 13 | Streamlit | 4 | Finance, Enduro, Cuisine |
| 14 | Configuration et secrets | 4 | Tous |
| 15 | Tâches planifiées et background jobs | 4 | Finance, Cuisine |
| 16 | Parsing de fichiers binaires (.fit) | 4 | Enduro |
| 17 | Appels LLM et function calling | 4 | Cuisine |
| 18 | Conception d'agents IA | 4 | Cuisine |
| 19 | Sécurité applicative de base | 4 | Tous |
| 20 | Packaging et Docker | 4 | Tous |
| 21 | Projet final transverse | 4 | Synthèse des 3 projets |

Le contenu reste modifiable et extensible à tout moment : voir « Ajouter ou compléter un chapitre ». Le mécanisme de badge « squelette » subsiste dans l'interface pour tout nouveau chapitre créé au statut `squelette`.

> Note : les exemples des chapitres purement Python (0-11) ont été exécutés et vérifiés. Ceux qui dépendent de services externes non disponibles hors ligne (IA/Azure OpenAI ch. 17-18, Docker ch. 20, vrais fichiers `.fit` ch. 16) suivent les API stables actuelles mais sont à valider à la première mise en pratique.

## Structure du projet

```
Application de learning/
├── app/
│   ├── main.py            # FastAPI : routes HTML + API de progression
│   ├── content.py         # découverte/chargement/validation des chapitres
│   ├── database.py        # SQLite : progression (exercices, projets)
│   ├── models.py          # schéma Pydantic du contenu (contrat des JSON)
│   ├── content/           # LE CONTENU — un dossier par chapitre
│   │   └── chapitre_XX_slug/
│   │       ├── chapitre.json     # métadonnées (obligatoire)
│   │       ├── theorie.md        # théorie Markdown (optionnel)
│   │       ├── exercices.json    # exercices (optionnel)
│   │       └── projet.json       # projet guidé (optionnel)
│   ├── templates/         # Jinja2 (base, index, chapitre)
│   ├── static/            # style.css, app.js (vanilla, zéro build)
│   └── data/
│       └── progress.db    # créée au premier lancement (gitignorée)
├── requirements.txt
└── README.md
```

## Ajouter ou compléter un chapitre

1. Créer un dossier `app/content/chapitre_NN_mon_slug/` (le nom du dossier est le slug de l'URL).
2. Y déposer au minimum `chapitre.json` ; ajouter `theorie.md`, `exercices.json`, `projet.json` selon l'avancement.
3. Recharger la page — c'est tout. Un fichier invalide n'empêche pas l'app de tourner : l'erreur est affichée sur la page d'accueil (et en détail sur la page du chapitre concerné).

### Schéma `chapitre.json`

```json
{
  "numero": 7,
  "titre": "Tests et qualité de code",
  "description": "Une phrase d'accroche.",
  "objectifs": ["...", "..."],
  "points_theorie": ["affichés tant que theorie.md n'existe pas"],
  "projets_cibles": ["Cuisine", "Finance", "Enduro"],
  "statut": "squelette"
}
```

`statut` : `"complet"` ou `"squelette"` (badge dans l'interface). `points_theorie` sert de plan de rédaction : la page chapitre l'affiche tant que `theorie.md` est absent.

### Schéma `exercices.json` (liste)

```json
[
  {
    "id": "ex01",
    "titre": "Titre court",
    "consigne": "Markdown (blocs de code ``` supportés).",
    "indices": ["Indice 1 (général)", "Indice 2", "Indice 3 (précis)"],
    "ressources": [{"titre": "venv — doc officielle", "url": "https://..."}],
    "solution": "Markdown : code commenté + explications."
  }
]
```

Les `id` doivent être uniques **dans le chapitre** (la progression est indexée par `(chapitre, id)` — renommer un id réinitialise sa progression). Champs `indices`/`ressources`/`solution` optionnels : les boutons correspondants n'apparaissent pas s'ils sont vides.

### Schéma `projet.json`

```json
{
  "titre": "Projet guidé",
  "consigne": "Markdown.",
  "etapes": ["Étape 1...", "Étape 2..."],
  "indices": ["..."],
  "ressources": [{"titre": "...", "url": "..."}],
  "solution": "Markdown."
}
```

Tous les champs texte (consignes, indices, étapes, solutions, théorie) sont du **Markdown** rendu côté serveur (code clôturé et tableaux supportés).

## API (utilisée par le front)

- `POST /api/progress/exercice` — corps `{"chapitre": "<slug>", "exercice_id": "ex01", "fait": true}`
- `POST /api/progress/projet` — corps `{"chapitre": "<slug>", "fait": true}`

## Notes techniques

- Python ≥ 3.10, dépendances volontairement minimales : FastAPI, Uvicorn, Jinja2, Markdown.
- Frontend vanilla (aucun framework JS, aucun build) ; le Markdown est rendu côté serveur.
- La base SQLite ne stocke que la progression — la supprimer ne touche jamais au contenu.
