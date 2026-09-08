---
name: theorie
description: Rédiger ou reprendre theorie.md pour un chapitre Python de cette application, à partir de ses objectifs, points_theorie et secteurs Cuisine, Finance ou Enduro. À utiliser avant les exercices et le projet.
allowed-tools: Read Grep Glob Edit Write
---

# Rédiger la théorie d'un chapitre

## Entrée et lectures obligatoires

Travaille depuis la racine du dépôt. Reçois le dossier
`app/content/chapitre_NN_slug/`, le sujet et les secteurs cibles. Lis son
`chapitre.json`, les fichiers déjà présents et le contrat dans `app/models.py`
(lecture seule). Si les métadonnées manquent, fais d'abord effectuer leur création
au statut `squelette` selon l'[orchestrateur](../../../agents/redacteur-chapitre.source.md).

Avant d'écrire, lis intégralement au moins un chapitre réellement abouti
(`chapitre.json`, `theorie.md`, `exercices.json`, `projet.json`), idéalement deux,
dans le même secteur. Le README distingue les références abouties du contenu à
reprendre : le seul champ `statut: complet` ne suffit pas. Les chapitres 1 et 2
sont les références initiales confirmées par l'utilisateur et ciblent `Tous`.
En l'absence de référence sectorielle aboutie, utilise-les ; ne présente pas
les chapitres 10, 11, 16, 17 ou 18 comme validés par défaut.

Lis également la théorie des chapitres antérieurs nécessaires : une notion ne
devient pas un prérequis parce qu'elle figure uniquement dans leur solution.

## Rédaction

- Écris uniquement `theorie.md`, en Markdown avec des sections `##` et des
  sous-sections si utiles. Texte pédagogique en français ; code en anglais
  (identifiants, docstrings, commentaires), fonctions et variables en
  `snake_case`, classes en `PascalCase`, conventions PEP 8.
- Public : ingénieur connaissant C/C++ et l'algorithmique, sans pratique
  réelle du développement. Explique la traduction vers Python et ses pièges,
  pas ce qu'est une boucle ou la POO en général.
- Garde la densité et le niveau d'explication des références. Ni simple
  catalogue d'API ni remplissage : chaque nouveauté reçoit une explication,
  un exemple métier, ses limites utiles et, si pertinent, une comparaison C++.
  Termine par une checklist concrète.
- Couvre tous les `objectifs` et chaque entrée de `points_theorie` quand la
  liste existe. Si elle est vide, construis le plan à partir des objectifs
  et de la demande, sans inventer de nouveau champ de métadonnées.
- Utilise les secteurs de `projets_cibles` : sous-ensemble non vide de
  `Cuisine`, `Finance`, `Enduro`, ou exclusivement `["Tous"]`. `Tous`
  signifie varier les exemples entre les trois secteurs, pas créer un secteur
  fictif. Choisis des données concrètes et des conventions explicites.
- Introduis toute API, syntaxe et dépendance nécessaire aux applications
  prévues : imports, décorateurs, annotations, exceptions, formats, options,
  méthodes auxiliaires. Une simple mention dans un tableau ne suffit pas
  si l'apprenant doit ensuite la mettre en œuvre.
- N'exige pas une notion d'un chapitre futur sans l'introduire ici avec
  suffisamment de détails. Préfère simplifier les exemples à ajouter des
  dépendances ou des abstractions hors sujet.
- Distingue les exemples autonomes des extraits à ajouter à une classe ou
  à une fonction. Indique les imports et les données nécessaires ; n'utilise
  pas de `...` dans un exemple présenté comme complet.

## Sortie et limites

Relis la couverture des objectifs et du plan. Transmets à l'orchestrateur les
sections écrites, les références consultées et les prérequis effectivement
introduits, afin de cadrer les exercices.

Ne modifie ni le moteur (`app/main.py`, `app/database.py`, `app/models.py`,
ni les fichiers homonymes), ni la progression, ni les autres chapitres.
Ne passe pas le statut à `complet` : seule la relecture de l'ensemble
théorie/exercices/projet peut autoriser cette transition.
N'exécute jamais le code des leçons ni celui de l'apprenant. Les exemples
et solutions restent du texte affiché à la demande, sans correction automatique
ni sandbox. Ne crée aucun commit et ne pousse rien.
