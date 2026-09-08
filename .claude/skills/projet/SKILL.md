---
name: projet
description: Rédiger projet.json, le projet guidé de fin d'un chapitre Python, après theorie.md et exercices.json. Mobiliser tous les acquis dans un secteur cible avec étapes, indices, ressources et solution sérialisés avec Python.
allowed-tools: Read Grep Glob Edit Write Bash
---

# Rédiger le projet guidé

## Préparation

Reçois le dossier `app/content/<cours>/chapitre_NN_slug/`.
Lis `chapitre.json`, `theorie.md`, `exercices.json`, le projet existant et
`app/models.py` (lecture seule). Lis aussi le projet d'un chapitre réellement
abouti identifié par le README, en privilégiant le même secteur. Les chapitres
1 et 2 du cours `python` (`Tous`) sont les références initiales confirmées ; ne prends pas un
ancien statut `complet` comme preuve suffisante.

Si la théorie ou les exercices manquent, fais d'abord appliquer `theorie`
puis `exercice`. Dresse une correspondance entre les objectifs, les sections
de théorie, les exercices et les étapes du futur projet.

## Contrat de sortie

`projet.json` contient **un seul objet**, avec exactement :

| Champ | Contenu |
|---|---|
| `titre` | Titre français décrivant le livrable et son secteur. |
| `consigne` | Markdown : contexte métier, résultat concret, données de départ, interface attendue, contraintes et cas limites. |
| `etapes` | Liste non vide de chaînes Markdown décrivant une progression guidée, de la modélisation à l'assemblage et à la relecture manuelle. |
| `indices` | 2 à 3 pistes progressives, du choix de conception au détail bloquant. |
| `ressources` | Liste non vide d'objets contenant exactement `titre` et `url` ; documentation Python française en priorité, puis Real Python ou documentation officielle spécialisée. |
| `solution` | Markdown : solution complète, code commenté, explications des choix. Le champ ne s'appelle jamais `correction`. |

Choisis **un** secteur de `projets_cibles` ; pour `["Tous"]`, choisis Cuisine,
Finance ou Enduro. Le projet doit mobiliser l'ensemble des acquis du chapitre,
pas seulement enchaîner des copies des exercices. Si les exercices couvrent
plusieurs secteurs, transpose leurs mécanismes dans ce contexte unique.
La difficulté supplémentaire vient de l'intégration, pas d'une API inconnue.

Écris en français hors code. Dans le code : noms, commentaires et docstrings
en anglais, `snake_case`, classes `PascalCase`, PEP 8. Les fichiers/méthodes
annoncés dans la consigne doivent correspondre exactement à la solution.
Indique les données et les imports nécessaires. Pas de solution avec `...`,
de « à implémenter » laissé au lecteur ou de dépendance implicite.

N'utilise pas une notion, fonction, méthode, syntaxe, option ou bibliothèque
absente de la théorie du chapitre et de celle des chapitres précédents,
y compris dans les étapes, indices, bonus et solution. Une ressource externe
ou une solution antérieure ne remplace pas une introduction pédagogique.
Au besoin, fais compléter la théorie et réaligner les exercices avant de
finaliser le projet.

## Sérialisation et relecture

Applique la méthode de [génération Python du skill exercice](../exercice/SKILL.md#genération-json-obligatoire),
avec un dictionnaire `project`, la destination `projet.json` et
`json.dump(project, output_file, ensure_ascii=False, indent=2)`.
Un script temporaire assemble et sérialise les chaînes ; il n'exécute aucun
code contenu dans ces chaînes. Ne maintiens pas une seconde source de contenu.

Recharge le fichier avec `json.load`. Contrôle les clés exactes, les types,
les étapes, les ressources et la présence d'une solution complète.
Relis la matrice théorie/exercices/projet et les résultats attendus.
Depuis la racine et avec l'environnement du projet, lance uniquement la
validation documentaire : `python -m agents.validate_chapter <cours> <slug>`.
Ce contrôle du JSON ne vérifie pas la cohérence pédagogique à ta place.

## Limites

Ne modifie ni moteur (`app/main.py`, `app/database.py`, `app/models.py`, ni
leurs homonymes), ni progression, ni schéma JSON, ni autres chapitres.
Un nouveau champ exigerait une décision explicite sur le README et le modèle
Pydantic ; ce n'est pas autorisé dans cette tâche.
N'exécute ni le code de l'apprenant ni les exemples ou solutions ; aucun
sandboxing ou mécanisme de validation automatique des réponses. Les indices,
ressources et solutions sont affichés à la demande par l'application existante.
Laisse l'orchestrateur décider du statut final après la relecture complète.
Ne crée aucun commit et ne pousse rien.
