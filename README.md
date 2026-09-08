# Hub Apprentissage — application locale multi-cours

Application web locale (FastAPI + SQLite) organisée en cours indépendants : théorie, exercices avec indices progressifs / ressources / correction commentée, et projet guidé de fin de chapitre. Le premier cours, **Apprendre Python**, comprend 22 chapitres progressifs, dont la rédaction est en cours, du setup macOS au déploiement Docker avec intégration IA. Les cours Microcontrôleurs & ESP32 et Impression 3D & Fusion 360 sont annoncés « bientôt disponible », sans contenu pour l'instant.

Le moteur est **totalement agnostique du contenu** : chaque cours vit dans `app/content/<cours>/`, avec ses chapitres en fichiers Markdown + JSON. Ajouter ou modifier un cours ou un chapitre ne demande aucune modification de code — ni même de redémarrage du serveur (le contenu est relu à chaque requête).

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

- **Accueil** (`/`) : hub des cours disponibles et à venir ; résumé des chapitres terminés pour les cours commencés. Les cartes « bientôt disponible » ne sont pas cliquables.
- **Page cours** (`/cours/python`, par exemple) : liste des chapitres avec statut (non commencé / en cours / terminé) et progression.
- **Page chapitre** : théorie en haut, puis exercices — chaque exercice propose des boutons *Indice 1/2/3* (révélés un par un), *Ressources* (liens externes) et *Voir la correction*.
- La progression se coche manuellement (checkbox « Terminé ») et est persistée par cours dans `app/data/progress.db` (SQLite). Aucune vérification automatique du code : tu testes dans VS Code, tu coches quand c'est fait.
- Le **projet guidé** de fin de chapitre se déverrouille quand tous les exercices du chapitre sont cochés.
- Réinitialiser la progression : supprimer `app/data/progress.db` (recréée au démarrage).

Au premier démarrage de la V2, l'ancienne progression est automatiquement
rattachée au cours `python`, sans perte des coches ni des dates. Cette migration
est transactionnelle et ne se répète pas aux démarrages suivants.

## État du contenu

Ce tableau concerne le cours Python, dans `app/content/python/`.

**Les chapitres 1 et 2 sont les références abouties confirmées par l'utilisateur.**
Le chapitre 3 a été rédigé avec l'agent à partir de ces références. Les autres
disposent déjà de contenu, mais restent à reprendre : la présence de quatre
fichiers ou un ancien `statut: "complet"` ne garantit pas que la rédaction
est aboutie. Les **22 chapitres (0 à 21)** contiennent
actuellement **104 exercices**, y compris ceux à reprendre.

| # | Chapitre | Ex. | Projet(s) cible | État de rédaction |
|---|---|---|---|---|
| 0 | Setup de l'environnement (macOS) | 6 | Tous | À reprendre |
| 1 | Fondamentaux Python | 6 | Tous | Référence utilisateur |
| 2 | Structures de données | 6 | Tous | Référence utilisateur |
| 3 | POO en Python | 6 | Tous | Rédigé par l'agent |
| 4 | Modules, exceptions et typing | 5 | Tous | À reprendre |
| 5 | Fichiers, JSON et context managers | 5 | Tous | À reprendre |
| 6 | SQLite avancé | 5 | Cuisine, Finance, Enduro | À reprendre |
| 7 | Tests et qualité de code | 5 | Tous | À reprendre |
| 8 | Async Python | 5 | Cuisine, Finance | À reprendre |
| 9 | Consommation d'API REST | 5 | Cuisine, Finance | À reprendre |
| 10 | Pandas | 5 | Finance, Enduro | À reprendre |
| 11 | Séries temporelles avec Pandas | 5 | Finance, Enduro | À reprendre |
| 12 | Visualisation de données | 4 | Finance, Enduro | À reprendre |
| 13 | Streamlit | 4 | Finance, Enduro, Cuisine | À reprendre |
| 14 | Configuration et secrets | 4 | Tous | À reprendre |
| 15 | Tâches planifiées et background jobs | 4 | Finance, Cuisine | À reprendre |
| 16 | Parsing de fichiers binaires (.fit) | 4 | Enduro | À reprendre |
| 17 | Appels LLM et function calling | 4 | Cuisine | À reprendre |
| 18 | Conception d'agents IA | 4 | Cuisine | À reprendre |
| 19 | Sécurité applicative de base | 4 | Tous | À reprendre |
| 20 | Packaging et Docker | 4 | Tous | À reprendre |
| 21 | Projet final transverse | 4 | Synthèse des 3 projets | À reprendre |

Le contenu reste modifiable et extensible à tout moment : voir « Ajouter ou compléter un chapitre ». Le mécanisme de badge « squelette » subsiste dans l'interface pour tout nouveau chapitre créé au statut `squelette`.

L'état éditorial de ce tableau est distinct du badge technique `statut` :
les anciens statuts restent inchangés tant que le chapitre n'est pas repris.
L'agent fait une relecture pédagogique et une validation des documents, **pas
d'exécution des exemples ou du code de l'apprenant**. Les mises en pratique
restent manuelles dans VS Code.

## Structure du projet

```
Application de learning/
├── app/
│   ├── main.py            # FastAPI : routes HTML + API de progression
│   ├── content.py         # découverte/chargement/validation des cours et chapitres
│   ├── database.py        # SQLite : progression (exercices, projets)
│   ├── models.py          # schéma Pydantic du contenu (contrat des JSON)
│   ├── content/           # LE CONTENU — un dossier par cours
│   │   ├── python/
│   │   │   ├── cours.json       # métadonnées du cours (obligatoire)
│   │   │   └── chapitre_XX_slug/ # 22 dossiers, du chapitre 00 au 21
│   │   │       ├── chapitre.json # métadonnées (obligatoire)
│   │   │       ├── theorie.md    # théorie Markdown (optionnel)
│   │   │       ├── exercices.json # exercices (optionnel)
│   │   │       └── projet.json   # projet guidé (optionnel)
│   │   ├── esp32-microcontroleurs/
│   │   │   └── cours.json       # statut a_venir, sans chapitre
│   │   └── impression-3d-fusion360/
│   │       └── cours.json       # statut a_venir, sans chapitre
│   ├── templates/         # Jinja2 (base, hub, cours, chapitre)
│   ├── static/            # style.css, app.js (vanilla, zéro build)
│   └── data/
│       └── progress.db    # créée au premier lancement (gitignorée)
├── tests/
│   └── test_multi_cours.py # migration, découverte, routes et isolation des cours
├── requirements.txt
└── README.md
```

## Ajouter ou compléter un chapitre

1. Dans un cours existant, créer un dossier `app/content/<cours>/chapitre_NN_mon_slug/` (le nom du dossier est le slug de l'URL, par exemple `/cours/python/chapitre/chapitre_01_fondamentaux`).
2. Y déposer au minimum `chapitre.json` ; ajouter `theorie.md`, `exercices.json`, `projet.json` selon l'avancement.
3. Recharger la page — c'est tout. Un fichier invalide n'empêche pas l'app de tourner : l'erreur est affichée sur le hub et la page du cours (et en détail sur la page du chapitre concerné).

Le numéro du chapitre doit être unique **dans son cours**. Deux cours peuvent
utiliser les mêmes numéros et slugs de chapitre sans partager leur progression.

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

`statut` : `"complet"` ou `"squelette"` (badge dans l'interface). `points_theorie` sert de plan de rédaction : la page chapitre l'affiche tant que `theorie.md` est absent. `projets_cibles` : sous-ensemble non vide de `["Cuisine", "Finance", "Enduro"]`, sans doublons, ou exclusivement `["Tous"]`.

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

Les `id` doivent être uniques **dans le chapitre** (la progression est indexée par `(cours, chapitre, id)` — renommer un cours, un chapitre ou un id dissocie sa progression). Champs `indices`/`ressources`/`solution` optionnels : les boutons correspondants n'apparaissent pas s'ils sont vides.

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

## Ajouter un cours

1. Créer `app/content/<slug>/cours.json` (le nom du dossier est le slug ; aucun champ `slug` dans le JSON).
2. Renseigner les métadonnées ci-dessous. Garder `statut: "a_venir"` tant qu'aucun chapitre n'existe : la carte est visible, atténuée et sans lien.
3. Ajouter les dossiers de chapitre dans ce cours, puis passer le statut à `"disponible"` lorsqu'il est prêt à être ouvert.
4. Recharger le hub : le cours est découvert automatiquement, sans modification de code ni redémarrage.

```json
{
  "ordre": 4,
  "titre": "Mon prochain cours",
  "description": "Les compétences à acquérir.",
  "icone": "📚",
  "statut": "a_venir"
}
```

`ordre` et `titre` sont obligatoires. Les cours sont triés par `ordre`.
`description` vaut `""` par défaut, `icone` vaut `"📚"` et `statut` vaut
`"disponible"` ; seuls `"disponible"` et `"a_venir"` sont acceptés.
Un dossier sans `cours.json` est ignoré. Des métadonnées invalides sont
signalées sur le hub sans empêcher les autres cours de s'afficher.

## Ajouter un chapitre via l'agent

**Adaptation V2 encore nécessaire :** `agents/redacteur-chapitre.source.md`
et les skills `theorie` / `exercice` / `projet` restent mono-cours et n'ont
pas été modifiés ici. Avant de relancer la rédaction, il faudra leur apprendre
les chemins `app/content/<cours>/...`, l'unicité du numéro par cours et la
nouvelle commande du validateur. Les instructions d'agent ci-dessous décrivent
donc le fonctionnement antérieur, à adapter avant de rédiger le prochain cours.

L'agent **`redacteur-chapitre`** fonctionne dans Claude Code et GitHub Copilot
dans VS Code. Il n'a besoin ni de Cowork ni d'un serveur MCP. Ouvrir la
**racine du dépôt** et utiliser l'environnement Python de l'application
(`source .venv/bin/activate`, Python ≥ 3.10, dépendances de `requirements.txt`).
Les abonnements/modèles disponibles et les permissions restent ceux du client.

### Source unique et adaptateurs

```text
.claude/skills/
├── theorie/SKILL.md
├── exercice/SKILL.md
└── projet/SKILL.md
.github/skills -> ../.claude/skills
.claude/agents/redacteur-chapitre.md
.github/agents/redacteur-chapitre.agent.md
agents/
├── redacteur-chapitre.source.md   # corps commun de l'orchestrateur
├── sync_redacteur.py             # recopie le corps, préserve les frontmatters
└── validate_chapter.py           # contrôle documentaire, sans exécution de code
```

Les skills sont les **mêmes fichiers**, via le lien symbolique. Ne crée pas
de copies dans `.github/skills`. Les adaptateurs ne diffèrent que par leur
frontmatter : Claude utilise `name`, `description`, `model`, `color` ;
Copilot utilise `description`, `tools`, `model`, `target: vscode`.
Claude hérite du modèle de la session. Copilot propose une liste de modèles
par ordre de préférence ; adapte seulement ce champ à ceux de ton sélecteur,
ou omets-le pour conserver le modèle sélectionné.

Le frontmatter `allowed-tools` des skills appartient au format Agent Skills,
mais son support est expérimental et ses noms d'outils ne sont pas universels.
Ce n'est **pas** un contrôle de permissions commun aux deux clients.
Copilot dispose des outils via son adaptateur ; les règles métier sont dans
les skills. Si l'invocation native d'un skill n'est pas disponible dans un
contexte d'agent, l'orchestrateur lit le même `SKILL.md` et l'applique.

### Depuis Claude Code

Après ajout des fichiers, redémarre la session si l'agent n'est pas découvert.
Lance `claude --agent redacteur-chapitre`, ou demande dans une session :

```text
Utilise l'agent redacteur-chapitre pour reprendre le chapitre 4
(chapitre_04_modules_exceptions_typing).
Sujet : modules, exceptions et typing. Secteurs : Tous.
Prends les chapitres 1 et 2 comme références de rédaction.
Conserve le slug et tous les IDs d'exercices existants.
```

Pour ne reprendre qu'une partie : `/theorie chapitre_04_modules_exceptions_typing`,
`/exercice chapitre_04_modules_exceptions_typing` ou
`/projet chapitre_04_modules_exceptions_typing`. Un skill isolé ne déclare
pas le chapitre complet ; demande l'orchestrateur pour la finalisation.

### Depuis GitHub Copilot dans VS Code

Utilise une version récente de VS Code et de Copilot prenant en charge les
[agents personnalisés](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
et les [Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills).
Dans Chat, choisis **`redacteur-chapitre`** dans le sélecteur d'agents puis
envoie le même texte que ci-dessus. Autorise la lecture, l'édition et les
commandes Python de génération/validation quand le client le demande.
Les skills sont aussi accessibles par `/theorie`, `/exercice`, `/projet`.

Si rien n'apparaît, recharge la fenêtre, contrôle la découverte dans
**Chat: Open Customizations**, les permissions du workspace et le lien :

```bash
readlink .github/skills
# ../.claude/skills
git ls-files -s .github/skills
# le mode doit être 120000, pas 100644
```

macOS/Linux prennent en charge ce lien directement. Sous Windows, utilise
WSL ou un checkout Git avec les liens symboliques activés (`core.symlinks=true`
et droits nécessaires). Un fichier texte contenant le chemin n'est pas un
lien exploitable. Les versions récentes de Copilot savent également découvrir
`.claude/skills` directement ; le lien demandé reste conservé pour le chemin
`.github/skills`, sans duplication.

### Déroulement et garanties

L'agent lit les métadonnées et les références abouties, passe le chapitre à
`squelette`, puis applique `theorie` → `exercice` → `projet`. Il génère les JSON
avec Python (`json.dump`, UTF-8, `ensure_ascii=False`, `indent=2`), relit chaque
notion utilisée par rapport à la théorie et aux chapitres précédents, puis
passe à `complet` et actualise le tableau de contenu. Les scripts temporaires
de génération sont supprimés ; les Markdown/JSON restent la source du cours.

Les IDs et le slug sont conservés : **une réécriture ne réinitialise pas la
progression déjà cochée**. L'agent ne modifie ni le moteur ni la base SQLite.
Il n'ajoute aucun champ aux modèles et n'exécute jamais les exemples,
solutions ou programmes de l'apprenant. `solution` est le nom exact du champ
JSON, même si l'interface parle de « correction ».

Le contrôle éditorial est plus strict que les champs optionnels du moteur :
4 à 6 exercices, 2 à 3 indices, ressources et solutions renseignées, clés
exactes et unicité des IDs. Pour le relancer, avec le venv activé :

```bash
python -m agents.validate_chapter python chapitre_03_poo
```

Les deux arguments positionnels sont le slug du cours puis celui du chapitre.
Cette commande charge les documents avec les modèles Pydantic existants et
le chargeur de l'application. Elle ne lance pas le code Markdown et ne remplace
pas la relecture des prérequis, des résultats et de la progression pédagogique.

Le premier essai de rédaction a été réalisé sur **le chapitre 3**, avec
`claude --agent redacteur-chapitre` et invocation native des trois skills,
puis relecture éditoriale. Ses six IDs sont conservés. Cet essai porte sur
Claude Code ; l'interface de sélection de l'agent dans VS Code n'a pas été
exercée ici.

### Faire évoluer l'agent

Modifie uniquement les skills sous `.claude/skills/`. Pour les règles
d'orchestration, modifie `agents/redacteur-chapitre.source.md`, puis :

```bash
python3 agents/sync_redacteur.py
python3 agents/sync_redacteur.py --check
```

Le corps est recopié à l'identique dans les deux adaptateurs ; leurs
frontmatters sont conservés. Versionne la source, les deux adaptateurs,
les trois skills, les scripts et le lien symbolique ensemble. Aucun commit
ni push n'est effectué automatiquement par l'agent.

## API (utilisée par le front)

- `POST /api/progress/exercice` — corps `{"cours": "python", "chapitre": "<slug>", "exercice_id": "ex01", "fait": true}`
- `POST /api/progress/projet` — corps `{"cours": "python", "chapitre": "<slug>", "fait": true}`

## Notes techniques

- Python ≥ 3.10, dépendances volontairement minimales : FastAPI, Uvicorn, Jinja2, Markdown.
- Frontend vanilla (aucun framework JS, aucun build) ; le Markdown est rendu côté serveur.
- La base SQLite ne stocke que la progression — la supprimer ne touche jamais au contenu.

Les tests du moteur s'exécutent avec `python -m unittest discover -s tests -v`.
Ils utilisent uniquement des contenus et bases temporaires, sans toucher à
la progression locale ni exécuter le code pédagogique ; aucune dépendance
de test supplémentaire n'est nécessaire.
