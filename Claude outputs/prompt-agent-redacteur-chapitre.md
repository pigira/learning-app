# Prompt à coller dans l'autre session — Agent "rédacteur de chapitre"

## Contexte

Tu travailles dans le repo "Application de learning" (FastAPI + SQLite, contenu en Markdown/JSON sous `app/content/`). Les 22 chapitres (0 à 21) sont déjà rédigés et servent de référence de style et de niveau de détail — avant d'écrire quoi que ce soit, lis au moins un chapitre déjà complet du même secteur que celui visé (ex. `chapitre_16_parsing_binaire` pour Enduro, `chapitre_10_pandas`/`chapitre_11_series_temporelles` pour Finance, `chapitre_17_llm_function_calling`/`chapitre_18_agents_ia` pour Cuisine).

Objectif : créer un agent "rédacteur de chapitre" composé de 3 skills (`theorie`, `exercice`, `projet`), utilisable **indifféremment depuis Claude Code et depuis GitHub Copilot dans VS Code**, sans dupliquer la logique métier entre les deux outils, et versionné dans le repo (pas une solution propriétaire à un seul outil).

## Architecture à créer

### Skills — contenu strictement identique entre les deux outils

Le format `SKILL.md` (frontmatter `name` / `description` / `allowed-tools`) est identique chez Claude Code et chez GitHub Copilot ; seul le chemin de découverte diffère :
- Claude Code lit `.claude/skills/<nom>/SKILL.md`
- GitHub Copilot lit `.github/skills/<nom>/SKILL.md`

Pour éviter toute duplication : crée les skills sous `.claude/skills/`, puis fais de `.github/skills` un lien symbolique vers `.claude/skills` (`ln -s ../.claude/skills .github/skills`). Vérifie que git suit bien le lien (`git add .github/skills` puis `git ls-files -s` doit afficher le mode `120000`).

3 skills à créer :
1. `.claude/skills/theorie/SKILL.md`
2. `.claude/skills/exercice/SKILL.md`
3. `.claude/skills/projet/SKILL.md`

### Agent orchestrateur — un seul, deux adaptateurs fins

Les schémas de frontmatter divergent entre les deux outils, donc pas de symlink possible ici :
- `.claude/agents/redacteur-chapitre.md` — frontmatter `name`, `description`, `model`, `color`
- `.github/agents/redacteur-chapitre.agent.md` — frontmatter `description`, `tools`, `model`, `target`

Rédige le corps de l'agent une seule fois et colle-le dans les deux fichiers (un seul agent, la duplication reste gérable manuellement). Si tu préfères éviter toute dérive future, garde aussi une version source dans `agents/redacteur-chapitre.source.md` et recopie-la dans les deux adaptateurs à chaque modification.

## Règles de contenu à injecter dans les skills (non négociables, tirées du schéma réel du repo)

### `chapitre.json` (rappel, déjà existant)
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
`statut` : `"complet"` ou `"squelette"`. `projets_cibles` : sous-ensemble de `["Cuisine", "Finance", "Enduro"]` ou `["Tous"]`. `points_theorie` sert de plan de rédaction tant que `theorie.md` n'existe pas.

### Skill `theorie` → `theorie.md`
- Markdown, sections `##`, texte pédagogique en français, exemples de code en anglais (snake_case, docstrings, conventions PEP8).
- Angle "traduction depuis C/C++" quand pertinent — public = ingénieur avec fond C/C++/algorithmique mais sans pratique dev réelle, pas de réexplication de concepts génériques.
- Dense, sans remplissage, même niveau de détail que les chapitres existants du secteur visé.
- Couvre chaque `point_theorie` du `chapitre.json` s'il y en a.

### Skill `exercice` → `exercices.json`
- Liste de 4 à 6 objets. Champs exacts : `id` (ex. `"ex01"`, unique dans le chapitre — ne jamais renommer un id existant, la progression est indexée dessus), `titre`, `consigne` (Markdown, blocs ` ``` ` supportés), `indices` (2 à 3, du général au précis), `ressources` (array de `{"titre":..., "url":...}`, priorité docs.python.org/fr puis Real Python), `solution` (Markdown, code commenté).
- ⚠️ Le champ s'appelle **`solution`**, pas `correction`.
- Exercices thématisés sur le(s) `projets_cibles` du chapitre — jamais d'exemples abstraits.
- Génère le JSON via un script Python (`json.dump(..., ensure_ascii=False, indent=2)`) plutôt que d'écrire le JSON à la main — évite les erreurs d'échappement sur les gros blocs Markdown multi-lignes.

### Skill `projet` → `projet.json`
- Un seul objet : `titre`, `consigne`, `etapes` (array, décrit la progression du projet guidé), `indices`, `ressources`, `solution`.
- Doit mobiliser l'ensemble de la théorie et des exercices du chapitre, dans le contexte d'un des projets cibles.
- Même génération via script Python que pour `exercice`.

## Comportement attendu de l'agent orchestrateur

Entrée : numéro/slug de chapitre + sujet + secteur(s) cible(s).

1. Lire le `chapitre.json` existant (ou squelette) ; s'il n'existe pas, le créer (`numero`, `titre`, `description`, `objectifs`, `points_theorie`, `projets_cibles`, `statut: "squelette"` au départ).
2. Lire 1-2 chapitres déjà complets du même secteur comme ancrage de style et de niveau de détail.
3. Skill `theorie` → rédiger `theorie.md`.
4. Skill `exercice` → générer `exercices.json`, cohérent avec `theorie.md` (rien d'utilisé qui n'y soit introduit, ni dans un chapitre antérieur).
5. Skill `projet` → générer `projet.json`.
6. Auto-relecture de cohérence (équivalent du skill Cowork `verif-coherence-chapitre`, à réintégrer ici en dur puisqu'il n'est pas portable hors Cowork) : toute notion/fonction/méthode/syntaxe utilisée dans `exercices.json` ou `projet.json` doit être introduite dans `theorie.md` du chapitre ou dans un chapitre antérieur — sinon corriger avant de terminer.
7. Passer `statut` à `"complet"` dans `chapitre.json`.
8. Mettre à jour le tableau du README (section `## État du contenu`) avec la nouvelle ligne.

## Contraintes à ne pas franchir

- Ne jamais modifier `app/main.py`, `database.py`, `models.py` (moteur figé, agnostique du contenu).
- Aucune exécution/vérification automatique du code utilisateur — uniquement indices/ressources/solution affichés à la demande. Ne pas réintroduire de sandboxing.
- Rester strictement dans le schéma JSON existant ; tout nouveau champ implique une mise à jour du README **et** du modèle Pydantic dans `models.py`.

## Ce qui est demandé à cette session

1. Créer l'arborescence ci-dessus (3 skills + agent + symlink Copilot).
2. Rédiger le contenu des 3 `SKILL.md` et de l'agent en respectant les règles ci-dessus.
3. Tester l'agent de bout en bout sur un chapitre concret (au choix : un squelette existant à compléter, ou un nouveau chapitre d'approfondissement sectoriel).
4. Documenter la procédure dans le README (nouvelle section "Ajouter un chapitre via l'agent").
