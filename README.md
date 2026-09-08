# Hub Apprentissage — application locale multi-cours

Application web locale (FastAPI + SQLite) organisée en cours indépendants : théorie, exercices avec indices progressifs / ressources / correction commentée, et projet guidé de fin de chapitre. Le premier cours, **Apprendre Python**, comprend 22 chapitres progressifs, dont la rédaction est en cours, du setup macOS au déploiement Docker avec intégration IA. Les cours Microcontrôleurs & ESP32 et Impression 3D & Fusion 360 sont annoncés « bientôt disponible », sans contenu pour l'instant. Le cours **Altitude Sports — Git et GitHub, de débutant à avancé** possède un squelette de 37 chapitres, sans leçons, exercices ni projets rédigés ; il reste également à venir.

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

## État du contenu — Apprendre Python

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

## État du contenu — Altitude Sports — Git et GitHub, de débutant à avancé

Ce tableau concerne le cours Git et GitHub, dans `app/content/git-github/`.
Les **37 chapitres (0 à 36)** sont au statut `squelette` et le cours reste
`a_venir`, dans l'attente de la validation du plan par Pierre puis de la rédaction.
Ils ciblent **Enduro**, avec une progression sans prérequis de programmation,
sur Windows, macOS et Linux, au terminal et dans VS Code.
Le fil rouge d'entreprise est décrit dans
[`agents/narrations/git-github.md`](agents/narrations/git-github.md).
Aucune théorie, aucun exercice et aucun projet guidé ne sont encore rédigés.

| # | Chapitre | Ex. | Projet(s) cible | État de rédaction |
|---|---|---|---|---|
| 0 | Altitude : l'accueil — Installation et orientation | 0 | Enduro | À rédiger |
| 1 | Altitude : le casier — Terminal et chemins de fichiers | 0 | Enduro | À rédiger |
| 2 | Altitude : le registre — Premier dépôt local | 0 | Enduro | À rédiger |
| 3 | Altitude : les premières fiches — Index et commits | 0 | Enduro | À rédiger |
| 4 | Altitude : la traçabilité — Historique et différences | 0 | Enduro | À rédiger |
| 5 | Altitude : le tri — Fichiers suivis et exclusions | 0 | Enduro | À rédiger |
| 6 | Altitude : la correction — Restaurer sans perdre le travail | 0 | Enduro | À rédiger |
| 7 | Altitude : les variantes — Branches et HEAD | 0 | Enduro | À rédiger |
| 8 | Altitude : le rapprochement — Fusion de branches | 0 | Enduro | À rédiger |
| 9 | Altitude : le désaccord — Résolution des conflits | 0 | Enduro | À rédiger |
| 10 | Altitude : le point de rencontre — GitHub et authentification | 0 | Enduro | À rédiger |
| 11 | Altitude : la passerelle — Dépôts distants, clone et push | 0 | Enduro | À rédiger |
| 12 | Altitude : les échanges — Fetch, pull et divergence | 0 | Enduro | À rédiger |
| 13 | Altitude : la table de relecture — Pull requests | 0 | Enduro | À rédiger |
| 14 | Altitude : le planning — Issues et organisation du travail | 0 | Enduro | À rédiger |
| 15 | Altitude : les partenaires — Forks et contributions externes | 0 | Enduro | À rédiger |
| 16 | Altitude : les règles communes — Workflows et gouvernance | 0 | Enduro | À rédiger |
| 17 | Altitude : l'interruption — Stash et worktrees | 0 | Enduro | À rédiger |
| 18 | Altitude : la mise au propre — Rebase et historique local | 0 | Enduro | À rédiger |
| 19 | Altitude : le correctif ciblé — Cherry-pick et revert | 0 | Enduro | À rédiger |
| 20 | Altitude : le filet de secours — Reflog et récupération | 0 | Enduro | À rédiger |
| 21 | Altitude : l'enquête — Blame, recherche et bisect | 0 | Enduro | À rédiger |
| 22 | Altitude : les coulisses — Objets et références Git | 0 | Enduro | À rédiger |
| 23 | Altitude : les trois postes — Portabilité et attributs | 0 | Enduro | À rédiger |
| 24 | Altitude : la médiathèque — Gros fichiers et clones ciblés | 0 | Enduro | À rédiger |
| 25 | Altitude : le kit partagé — Dépendances et submodules | 0 | Enduro | À rédiger |
| 26 | Altitude : la fiche de contrôle — YAML et vérifications shell | 0 | Enduro | À rédiger |
| 27 | Altitude : le contrôle automatique — Premiers workflows Actions | 0 | Enduro | À rédiger |
| 28 | Altitude : les contrôles croisés — Matrices, artefacts et caches | 0 | Enduro | À rédiger |
| 29 | Altitude : la zone protégée — Sécurité des automatisations | 0 | Enduro | À rédiger |
| 30 | Altitude : la sortie de saison — Tags et releases | 0 | Enduro | À rédiger |
| 31 | Altitude : la vitrine — Documentation et GitHub Pages | 0 | Enduro | À rédiger |
| 32 | Altitude : le tableau de bord — GitHub CLI et API | 0 | Enduro | À rédiger |
| 33 | Altitude : les habilitations — Accès et signatures | 0 | Enduro | À rédiger |
| 34 | Altitude : l'alerte — Prévention et réponse aux incidents | 0 | Enduro | À rédiger |
| 35 | Altitude : la continuité — Sauvegarde et maintenance | 0 | Enduro | À rédiger |
| 36 | Altitude : la saison complète — Projet final transverse | 0 | Enduro | À rédiger |

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
│   │   ├── impression-3d-fusion360/
│   │   │   └── cours.json       # statut a_venir, sans chapitre
│   │   └── git-github/
│   │       ├── cours.json       # statut a_venir, ordre 4
│   │       └── chapitre_NN_slug/ # 37 dossiers, du chapitre 00 au 36
│   │           └── chapitre.json # statut squelette, métadonnées seules
│   ├── templates/         # Jinja2 (base, hub, cours, chapitre)
│   ├── static/            # style.css, app.js (vanilla, zéro build)
│   └── data/
│       └── progress.db    # créée au premier lancement (gitignorée)
├── tests/
│   ├── test_agents.py      # synchronisation et validation des squelettes
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
2. Renseigner les métadonnées ci-dessous. Garder `statut: "a_venir"` tant qu'aucun chapitre n'est rédigé, même si des squelettes existent : la carte est visible, atténuée et sans lien.
3. Ajouter les dossiers de chapitre dans ce cours, puis passer manuellement le statut à `"disponible"` lorsqu'au moins un chapitre est `complet` et que le cours est prêt à être ouvert. L'architecte n'effectue jamais cette ouverture.
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

## Ajouter un cours ou un chapitre via les agents

**`architecte-cours`** conçoit d'abord les métadonnées et l'enchaînement des
chapitres. Après validation du squelette par Pierre, **`redacteur-chapitre`**
rédige un chapitre à la fois avec les trois skills existants. Pour reprendre
un chapitre déjà cadré, utiliser directement le rédacteur en indiquant le cours.

Les deux agents fonctionnent dans Claude Code et GitHub Copilot
dans VS Code. Ils n'ont besoin ni de Cowork ni d'un serveur MCP. Ouvrir la
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
.claude/agents/architecte-cours.md
.claude/agents/redacteur-chapitre.md
.github/agents/architecte-cours.agent.md
.github/agents/redacteur-chapitre.agent.md
agents/
├── architecte-cours.source.md    # conception du squelette, sans rédaction
├── redacteur-chapitre.source.md  # orchestration des trois skills de rédaction
├── sync_agents.py               # synchronise tous les agents, préserve les frontmatters
├── validate_course_skeleton.py  # contrôle des seules métadonnées
├── validate_chapter.py          # contrôle des quatre documents d'un chapitre rédigé
└── narrations/                  # bibles optionnelles <cours>.md, hors contenu applicatif
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
contexte d'agent, l'agent lit le même `SKILL.md` et l'applique. L'architecte
n'utilise que le contrat d'entrée de `theorie` ; il n'en lance pas la rédaction
et ne nécessite aucun skill supplémentaire.

### Concevoir un nouveau cours avec architecte-cours

Fournir le **slug du cours**, existant en `a_venir` ou nouveau, et décrire ce
que tu veux apprendre, ton niveau réel sur le sujet, le matériel exact
(références et quantités) et les logiciels possédés. Préciser la profondeur,
le nombre de chapitres ou le temps disponible si connu, les usages personnels
visés, et une éventuelle trame narrative. L'agent pose les questions manquantes
avant toute écriture ; il ne déduit pas une expérience matérielle d'un bagage C/C++.

Exemple fictif d'entrée complète, à adapter à ton besoin :

```text
Utilise l'agent architecte-cours pour le nouveau cours statistiques-appliquees.
Je veux analyser des séries de mesures pour mes projets Enduro.
Je connais les bases Python mais débute en statistiques.
Matériel et logiciels : mon Mac avec VS Code et Python déjà installés ;
les données seront synthétiques, aucun capteur ni achat à prévoir.
Vise 8 chapitres, du setup à un projet final transverse d'analyse.
Trame narrative souhaitée : une enquête d'atelier autour de mesures incohérentes.
Crée seulement cours.json et les chapitre.json au statut squelette,
la table README du cours et une bible narrative si nécessaire.
Ne lance pas redacteur-chapitre : je veux d'abord valider le squelette.
```

Dans Claude Code : `claude --agent architecte-cours`, ou demander son utilisation
dans une session. Dans Copilot VS Code : sélectionner `architecte-cours`, puis
envoyer le même texte. Si l'agent n'a pas d'outil de dialogue dans son contexte,
il remonte ses questions à la session appelante au lieu d'inventer les réponses.

La **trame narrative est optionnelle**. Dans les JSON, elle vit uniquement
dans `titre` (nom en univers et sous-titre technique) et `description`
(une phrase narrative, une technique), pour le cours et ses chapitres.
`objectifs` et `points_theorie` restent techniques et observables. Une bible
plus longue va dans `agents/narrations/<cours>.md`, note pour les agents
jamais chargée par le moteur. Aucun nouveau champ JSON n'est ajouté.
`projets_cibles` reste Cuisine, Finance, Enduro ou exclusivement Tous :
ce sont les projets personnels transversaux, pas les domaines des cours.

L'architecte s'ancre sur les métadonnées de cours existants et découpe une
progression du setup à un projet final transverse, avec des numéros à partir
de 0, uniques dans le cours. Il sérialise uniquement `cours.json` et les
`chapitre.json` en UTF-8 (`json.dump`, `ensure_ascii=False`, `indent=2`).
Le cours reste `a_venir`, les nouveaux chapitres restent `squelette` ; aucun
`theorie.md`, `exercices.json` ni `projet.json` n'est créé.

Pour contrôler le squelette, depuis la racine et avec le venv activé :

```bash
python -m agents.validate_course_skeleton statistiques-appliquees
```

Le validateur exige un cours avec au moins un `chapitre.json`, les champs
exacts de `CoursMeta` et `ChapitreMeta`, les types stricts, des objectifs et
un plan non vides, des numéros non négatifs sans doublon dans ce cours et
des secteurs valides. Il ne charge ni n'exige les documents de rédaction et
n'appelle pas `content.obtenir_chapitre`. Il peut aussi relire les métadonnées
d'un cours partiellement rédigé, sans modifier ses statuts. Comme le validateur
de chapitre, il n'exécute aucun exemple, solution ou programme matériel.

L'architecte restitue le plan et **une invocation complète du rédacteur par
chapitre**, avec le slug du cours et celui du chapitre. Pierre valide le
squelette avant de les lancer. Les invocations sont utilisables dans des sessions
indépendantes ; les métadonnées antérieures figent le plan, mais ne remplacent
pas une théorie enseignée. En parallèle, le rédacteur lit les théories déjà
disponibles et introduit localement les prérequis manquants, ou signale un
blocage au lieu de les supposer acquis. Il ne réécrit pas les autres chapitres.

### Convention État du contenu par cours

Chaque cours ébauché possède sa propre section
`## État du contenu — <titre du cours>` identifiant `app/content/<cours>/`.
L'architecte ajoute la table dès la livraison des squelettes, sans attendre
que le cours soit disponible :

| # | Chapitre | Ex. | Projet(s) cible | État de rédaction |
|---|---|---|---|---|
| 0 | Titre du premier chapitre | 0 | Secteurs retenus | À rédiger |

Toutes les nouvelles lignes commencent à **À rédiger**, avec **0 exercice**
(les 4 à 6 exercices futurs ne sont pas comptés). Le rédacteur actualise
uniquement la ligne de son chapitre dans la table de son cours, avec le nombre
réel d'exercices et l'état éditorial, sans toucher aux autres tables.
Lors de rédactions parallèles, relire la ligne avant édition et préserver les
mises à jour concurrentes ; ne pas remplacer une copie ancienne du README entier.
L'état éditorial reste distinct du statut technique `squelette` / `complet`.

### Depuis Claude Code

Après ajout des fichiers, redémarre la session si l'agent n'est pas découvert.
Lance `claude --agent redacteur-chapitre`, ou demande dans une session :

```text
Utilise l'agent redacteur-chapitre dans le cours python pour reprendre le chapitre 4
(chapitre_04_modules_exceptions_typing).
Sujet : modules, exceptions et typing. Secteurs : Tous.
Prends les chapitres 1 et 2 comme références de rédaction.
Conserve le slug et tous les IDs d'exercices existants.
```

Pour ne reprendre qu'une partie : `/theorie app/content/python/chapitre_04_modules_exceptions_typing/`,
`/exercice app/content/python/chapitre_04_modules_exceptions_typing/` ou
`/projet app/content/python/chapitre_04_modules_exceptions_typing/`. Un skill isolé ne déclare
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

Le rédacteur lit les métadonnées et les références abouties, passe le chapitre à
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

### Faire évoluer un agent

Modifie uniquement les skills sous `.claude/skills/`. Pour les règles
d'orchestration, modifie `agents/<nom>.source.md`, puis :

```bash
python3 agents/sync_agents.py
python3 agents/sync_agents.py --check
```

Le script découvre tous les `agents/*.source.md` et recopie chaque corps dans
les adaptateurs existants `.claude/agents/<nom>.md` et
`.github/agents/<nom>.agent.md` ; leurs frontmatters sont conservés.
Un adaptateur absent est ignoré silencieusement, jamais créé automatiquement.
Pour un nouvel agent, créer explicitement les adaptateurs des clients visés
avec leurs frontmatters, puis lancer la synchronisation.
`--check` ne modifie rien et termine avec le code 1 si un corps diverge.
Versionne les sources, leurs adaptateurs, les trois skills, les scripts et
le lien symbolique ensemble. Aucun commit
ni push n'est effectué automatiquement par l'agent.

## API (utilisée par le front)

- `POST /api/progress/exercice` — corps `{"cours": "python", "chapitre": "<slug>", "exercice_id": "ex01", "fait": true}`
- `POST /api/progress/projet` — corps `{"cours": "python", "chapitre": "<slug>", "fait": true}`

## Notes techniques

- Python ≥ 3.10, dépendances volontairement minimales : FastAPI, Uvicorn, Jinja2, Markdown.
- Frontend vanilla (aucun framework JS, aucun build) ; le Markdown est rendu côté serveur.
- La base SQLite ne stocke que la progression — la supprimer ne touche jamais au contenu.

Les tests du moteur et des outils d'agents s'exécutent avec `python -m unittest discover -s tests -v`.
Ils utilisent uniquement des contenus et bases temporaires, sans toucher à
la progression locale ni exécuter le code pédagogique ; aucune dépendance
de test supplémentaire n'est nécessaire.
