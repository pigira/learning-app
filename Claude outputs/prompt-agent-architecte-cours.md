# Prompt à coller dans l'autre session — Agent "architecte de cours"

## Contexte

Repo "Application de learning" (FastAPI + SQLite, contenu Markdown/JSON sous
`app/content/`), hub multi-cours depuis l'évolution V2
(`Claude outputs/prompt-evolution-multi-cours.md`). Trois cours existent :
`python/` (disponible, 22 chapitres), `esp32-microcontroleurs/` et
`impression-3d-fusion360/` (`a_venir`, `cours.json` seul, aucun chapitre).

L'agent **`redacteur-chapitre`** (`agents/redacteur-chapitre.source.md` +
skills `theorie`/`exercice`/`projet`) sait déjà rédiger le contenu complet
d'**un** chapitre existant. Il ne sait pas concevoir la liste des chapitres
d'un nouveau cours, ni leur enchaînement pédagogique. C'est le trou à
combler : un agent en amont qui, à partir de ce que Pierre veut apprendre
(sujet, matériel en sa possession, éventuellement une trame narrative), pose
les questions nécessaires puis génère le squelette complet du cours —
`cours.json` + un `chapitre.json` par chapitre — sans écrire `theorie.md`,
`exercices.json` ni `projet.json`. Une fois le squelette validé par Pierre,
`redacteur-chapitre` est invoqué chapitre par chapitre, en parallèle,
exactement comme aujourd'hui sur `python/`.

**Dette V2 à solder avant de construire quoi que ce soit sur un nouveau
cours** — signalée dans le README (section « Ajouter un chapitre via
l'agent ») et dans `prompt-evolution-multi-cours.md` (point 8) : l'agent
`redacteur-chapitre` et ses trois skills raisonnent encore comme si un seul
cours existait. Sans cette correction, le nouvel agent produirait des
squelettes corrects mais `redacteur-chapitre` les rédigerait au mauvais
chemin, avec une unicité de `numero` mal vérifiée et une commande de
validation invalide. Fais cette correction en premier (partie 1), le reste
en dépend directement.

Lis avant de commencer : `README.md` (sections « Ajouter un cours »,
« Ajouter un chapitre via l'agent », schéma `chapitre.json`),
`app/content.py`, `app/models.py`, `agents/redacteur-chapitre.source.md`,
les trois `SKILL.md`, `agents/validate_chapter.py`, et `cours.json` des
trois cours existants.

## Partie 1 — Corriger la dette mono-cours (prérequis bloquant)

Chemins et unicité de `numero` doivent devenir relatifs au cours, pas au
dépôt entier. Corrections précises, sans rien réécrire d'autre :

- `agents/redacteur-chapitre.source.md` :
  - « Son dossier doit rester un enfant direct de `app/content/` » →
    enfant direct de `app/content/<cours>/`.
  - « Le numéro est un entier unique dans le dépôt » → unique **dans son
    cours** (deux cours peuvent réutiliser les mêmes numéros, comme documenté
    dans « Ajouter ou compléter un chapitre » du README).
  - L'entrée de l'agent doit inclure le **slug du cours**, pas seulement le
    numéro/slug de chapitre et le sujet.
  - `lance python -m agents.validate_chapter <slug>` → deux arguments
    positionnels, cours puis slug (déjà le cas dans
    `agents/validate_chapter.py`, seul le texte de l'agent est en retard).
  - Étape 8 (README) : la mise à jour cible la table `## État du contenu`
    **du cours concerné** (voir partie 4 pour la convention par cours), pas
    implicitement celle de `python/`.
- `.claude/skills/theorie/SKILL.md` ligne ~12 : `app/content/chapitre_NN_slug/`
  → `app/content/<cours>/chapitre_NN_slug/`.
- `.claude/skills/exercice/SKILL.md` et `.claude/skills/projet/SKILL.md` :
  `python -m agents.validate_chapter <slug>` → `<cours> <slug>`.
- Repasse `python3 agents/sync_redacteur.py` (ou son remplaçant, partie 2)
  pour propager le corps corrigé dans les deux adaptateurs.
- Supprime l'avertissement « Adaptation V2 encore nécessaire » en tête de
  la section README « Ajouter un chapitre via l'agent » une fois fait.

Ne touche à rien d'autre dans ces fichiers : les règles de contenu
(`theorie`/`exercice`/`projet`, champs JSON, interdictions) restent
inchangées et s'appliquent identiquement à tous les cours.

## Partie 2 — Généraliser le script de synchronisation

`agents/sync_redacteur.py` est câblé sur un seul agent. Un deuxième agent
arrive ici, d'autres suivront (l'app est prévue pour accueillir d'autres
modules d'apprentissage). Remplace-le par `agents/sync_agents.py`,
générique :

- Découvre tous les `agents/*.source.md`.
- Pour chaque source `<nom>.source.md`, synchronise le corps vers
  `.claude/agents/<nom>.md` et `.github/agents/<nom>.agent.md` s'ils
  existent (ne crée pas les adaptateurs manquants — un agent sans adaptateur
  pour un client donné est possible, ignore-le silencieusement pour ce
  client-là plutôt que d'échouer).
- Conserve le comportement de `sync_redacteur.py` par ailleurs : frontmatter
  préservé, `--check` en code de sortie 1 si un corps diverge.
- Supprime `agents/sync_redacteur.py`, adapte le README (section « Faire
  évoluer l'agent » → généralise en « Faire évoluer un agent »,
  `python3 agents/sync_redacteur.py` → `python3 agents/sync_agents.py`,
  éventuellement avec `--agent <nom>` si tu veux permettre une synchro
  ciblée, sinon synchronise tout par défaut).

## Partie 3 — Nouvel agent `architecte-cours`

Même architecture que `redacteur-chapitre` : une source commune, deux
adaptateurs fins.

```text
agents/architecte-cours.source.md
.claude/agents/architecte-cours.md         # frontmatter: name, description, model, color
.github/agents/architecte-cours.agent.md   # frontmatter: description, tools, model, target: vscode
```

Utilise le même mécanisme de repli skill que `redacteur-chapitre` (lire le
`SKILL.md` directement si l'invocation native n'est pas disponible dans le
contexte d'agent) — mais `architecte-cours` n'a pas besoin de skill dédié :
son unique livrable (`chapitre.json` par chapitre + `cours.json`) est un
sous-ensemble de ce que le skill `theorie` sait déjà lire en entrée. Ne crée
pas de quatrième skill pour ça, ce serait dupliquer le schéma pour rien.

### Entrée

Slug de cours (existant en `a_venir`, ou nouveau — dans ce cas crée d'abord
`cours.json` selon la section « Ajouter un cours » du README) et une
description libre de Pierre : ce qu'il veut apprendre, le matériel/logiciel
déjà en sa possession, son niveau de départ sur le sujet, un nombre de
chapitres visé ou un temps disponible si mentionné, et — optionnel — une
trame narrative (ex. escape game).

### Comportement attendu

1. **Cadrage.** Si le sujet, le périmètre ou le matériel disponible sont
   flous, pose des questions précises avant d'écrire quoi que ce soit :
   quel matériel exact (références, quantités), quel niveau de départ réel
   sur ce sujet précis (le fond C/C++ ne présume pas d'expérience matérielle),
   combien de chapitres ou quelle profondeur, y a-t-il une trame narrative
   voulue et si oui laquelle. Ne devine pas le matériel ; demande-le.
2. **Ancrage.** Lis `cours.json` et les `chapitre.json` (métadonnées
   seulement, pas `theorie.md`) de 1 à 2 cours existants pour calibrer le
   niveau de détail attendu de `titre`, `description`, `objectifs`,
   `points_theorie` — la progression `python/` (chapitre 00 setup →
   fondamentaux → approfondissements → chapitre final transverse) est le
   patron de forme, pas de contenu.
3. **Conception pédagogique.** Découpe le sujet en une suite de chapitres
   allant d'un point de départ réaliste compte tenu du matériel/niveau
   déclarés jusqu'à un chapitre final qui mobilise l'ensemble des acquis
   dans un projet transverse, sur le modèle de `chapitre_21_projet_final`.
   Chaque chapitre a un périmètre autonome et vérifiable (des `objectifs`
   observables), sans dépendre d'un chapitre qui n'existe pas encore dans le
   même cours.
4. **Trame narrative, si demandée.** La fiction vit uniquement dans `titre`
   (nom en univers + sous-titre technique réel, ex. « Salle 3 — Le
   verrou GPIO ») et `description` (une phrase de narration, une phrase
   technique) de `cours.json` et de chaque `chapitre.json`. `objectifs` et
   `points_theorie` restent strictement techniques et observables, sans
   habillage narratif : c'est ce que lira `redacteur-chapitre` pour rédiger
   `theorie.md`, la relecture de cohérence qu'il applique ne doit pas avoir
   à démêler de la fiction. Si la trame nécessite une bible (personnages,
   règles d'univers, énigmes prévues par chapitre) plus longue qu'une
   phrase, écris-la dans `agents/narrations/<cours>.md` — **hors de
   `app/content/`**, donc jamais lu par le moteur ni par `content.py` :
   c'est une note de travail pour toi-même et pour `redacteur-chapitre`, pas
   du contenu applicatif.
5. **`projets_cibles` reste l'énumération existante.** Ce champ désigne les
   3 projets personnels cibles de Pierre (`Cuisine`, `Finance`, `Enduro`,
   ou `Tous`), transversaux à tous les cours — pas le domaine du cours
   lui-même. Un chapitre ESP32 peut très bien viser `Enduro` (un boîtier de
   mesure pour Enduro) ou `Cuisine` (un afficheur de minuterie). N'invente
   pas d'autre énumération et ne touche pas à
   `agents/validate_chapter.py`, qui la vérifie déjà en dur.
6. **Génération.** Pour chaque chapitre retenu, crée
   `app/content/<cours>/chapitre_NN_slug/chapitre.json` par sérialisation
   Python (`json.dump`, `ensure_ascii=False`, `indent=2`) avec exactement
   les champs `numero` (entier unique dans ce cours, à partir de 0),
   `titre`, `description`, `objectifs`, `points_theorie`, `projets_cibles`,
   `statut: "squelette"`. N'écris ni `theorie.md`, ni `exercices.json`, ni
   `projet.json` : ce n'est pas ton rôle, laisse `redacteur-chapitre` s'en
   charger chapitre par chapitre. Si `cours.json` doit être créé ou mis à
   jour (titre, description, icône), fais-le ; laisse `statut: "a_venir"`
   tant qu'aucun chapitre n'est passé à `"complet"` par `redacteur-chapitre`
   — ce n'est pas à toi de le faire passer à `"disponible"`.
7. **Auto-contrôle structurel.** Charge chaque `chapitre.json` généré avec
   `ChapitreMeta` (`app/models.py`) pour vérifier les champs exacts, l'unicité
   de `numero` dans le cours et la validité de `projets_cibles`, plutôt que
   de te fier à une relecture visuelle. `agents/validate_chapter.py` ne
   convient pas ici : il exige `theorie.md`/`exercices.json`/`projet.json`,
   qui n'existent pas encore à ce stade. Ajoute pour ça
   `agents/validate_course_skeleton.py <cours>` (voir partie 4) et lance-le
   avant de conclure.
8. **Restitution.** Liste les chapitres créés (numéro, titre, slug,
   `projets_cibles`), résume l'arc pédagogique et la trame narrative en
   quelques lignes, et donne à Pierre le texte exact à coller pour lancer
   `redacteur-chapitre` sur chaque chapitre — pensé pour un lancement en
   parallèle (une invocation par chapitre, indépendantes les unes des
   autres puisque chaque chapitre ne dépend que de la théorie des chapitres
   de numéro inférieur, déjà figée dans les squelettes). Rappelle que
   `redacteur-chapitre` doit recevoir le slug du cours en plus du chapitre.

### Interdictions permanentes

Identiques à `redacteur-chapitre` : jamais `app/main.py`, `app/database.py`,
`app/models.py` ni la base `app/data/progress.db` ; jamais de nouveau champ
JSON sans le discuter explicitement avec Pierre (ni pour porter la narration,
ni pour autre chose) ; aucune exécution de code, y compris du matériel
mentionné (pas de flash de firmware, pas d'accès série) ; aucun commit, push,
ni changement de branche sans demande explicite. Spécifique à cet agent : ne
rédige jamais `theorie.md`, `exercices.json` ou `projet.json`, et ne passe
jamais un `statut` de chapitre à `"complet"` — ce sont les seules décisions
qui appartiennent à `redacteur-chapitre`.

## Partie 4 — Validateur de squelette

`agents/validate_course_skeleton.py` (nouveau, à côté de
`validate_chapter.py`) :

```text
python -m agents.validate_course_skeleton <cours>
```

Charge `cours.json` (modèle `CoursMeta`), itère les `chapitre.json` du
dossier (modèle `ChapitreMeta`, champs exacts comme dans
`validate_chapter.py`), vérifie l'unicité de `numero` dans le cours et la
validité de `projets_cibles`. N'exige ni `theorie.md`, ni `exercices.json`,
ni `projet.json`, et n'appelle pas `content.obtenir_chapitre` (qui suppose
un chapitre chargeable en entier). Documentaire et structurel uniquement,
comme son homologue — aucune exécution de code.

## Partie 5 — README

- Retire l'avertissement de dette V2 (partie 1).
- Section « Ajouter un chapitre via l'agent » → généralise en couvrant les
  deux agents (`architecte-cours` puis `redacteur-chapitre`), un même
  schéma source/adaptateurs pour les deux, une seule commande de synchro
  (`agents/sync_agents.py`).
- Ajoute une sous-section « Concevoir un nouveau cours avec
  `architecte-cours` » : entrée attendue, exemple d'invocation, rappel que
  la trame narrative est optionnelle et vit dans `titre`/`description` (+
  `agents/narrations/<cours>.md` si besoin d'une bible).
- Convention « État du contenu » par cours : tant qu'un cours n'a que des
  squelettes, une table `## État du contenu — <titre du cours>` symétrique
  à celle de `python/` (colonnes `#`, Chapitre, Ex., Projet(s) cible, État
  de rédaction, tout à `À rédiger` au départ) est ajoutée par
  `architecte-cours` à la restitution ; `redacteur-chapitre` la met à jour
  chapitre par chapitre comme il le fait déjà pour `python/`.

## Ce qui est demandé à cette session

1. Partie 1 : corriger `redacteur-chapitre.source.md` et les 3 skills pour
   le multi-cours, resynchroniser, mettre à jour le README en conséquence.
2. Partie 2 : remplacer `sync_redacteur.py` par `sync_agents.py`.
3. Partie 3 : créer `agents/architecte-cours.source.md` + les deux
   adaptateurs, en respectant le comportement et les interdictions décrits
   ci-dessus.
4. Partie 4 : créer `agents/validate_course_skeleton.py`.
5. Partie 5 : mettre à jour le README.
6. Tester `architecte-cours` de bout en bout sur `esp32-microcontroleurs`
   (matériel et trame à demander à Pierre en direct, ne rien inventer à sa
   place) pour produire un squelette complet, validé par
   `validate_course_skeleton.py`. Ne pas enchaîner sur `redacteur-chapitre`
   dans ce même test — Pierre valide le squelette avant toute rédaction de
   contenu.

## Definition of done

- [ ] `redacteur-chapitre` et ses 3 skills référencent `app/content/<cours>/…`
      et une unicité de `numero` par cours ; `sync_agents.py --check` passe.
- [ ] `architecte-cours` existe dans `.claude/agents/` et `.github/agents/`,
      corps identique, frontmatters propres à chaque client.
- [ ] `agents/validate_course_skeleton.py esp32-microcontroleurs` passe sur
      un squelette réel généré par l'agent, sans `theorie.md`/`exercices.json`/
      `projet.json`.
- [ ] Le squelette produit couvre `esp32-microcontroleurs` du matériel
      déclaré par Pierre jusqu'à un chapitre final transverse, avec une
      trame narrative si demandée, sans nouveau champ JSON.
- [ ] README à jour (dette V2 retirée, nouvelle section architecte-cours,
      convention État du contenu par cours documentée).
