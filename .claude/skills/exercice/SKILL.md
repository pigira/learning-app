---
name: exercice
description: Créer ou reprendre les 4 à 6 exercices thématiques de exercices.json après la théorie d'un chapitre Python. Préserver les IDs de progression, fournir indices progressifs, ressources et solution, et sérialiser avec Python.
allowed-tools: Read Grep Glob Edit Write Bash
---

# Rédiger les exercices

## Avant d'écrire

Reçois le dossier `app/content/<cours>/chapitre_NN_slug/`.
Lis `chapitre.json`, toute la théorie du chapitre, les exercices et le projet
existants, le contrat `app/models.py` (lecture seule), ainsi qu'un chapitre
réellement abouti de référence identifié dans le README. Les chapitres 1 et 2 du cours `python`
sont les références initiales ; `statut: complet` seul ne prouve pas qu'un
chapitre est abouti. Privilégie le même secteur, ou ces références `Tous`.
Si `theorie.md` manque ou est insuffisant, utilise d'abord `theorie`.

Relève la liste exacte des IDs existants avant toute modification. Ne renomme
ni ne supprime un ID existant : SQLite indexe la progression par `(slug, id)`.
Conserve autant que possible l'intention et l'ordre des exercices existants.
Si le contenu existant ne peut respecter ces contraintes et la limite de 4 à 6
exercices, signale le conflit et demande une décision, sans réinitialiser
implicitement la progression.

## Contrat de sortie

`exercices.json` est une **liste de 4 à 6 objets**, sans enveloppe. Chaque objet
contient exactement :

| Champ | Contenu |
|---|---|
| `id` | Chaîne unique dans ce chapitre, par exemple `ex01`. Préserver les IDs existants ; pour un ajout, choisir un ID non utilisé. |
| `titre` | Titre français précis et contextualisé. |
| `consigne` | Markdown : objectif, données d'entrée, comportement attendu, contraintes et cas limites. Blocs clôturés pris en charge. |
| `indices` | 2 à 3 chaînes Markdown, du principe général à une indication précise, sans donner d'emblée toute la solution. |
| `ressources` | Liste non vide d'objets contenant exactement `titre` et `url`. Priorité à `docs.python.org/fr`, puis Real Python ; documentation officielle de la bibliothèque concernée si nécessaire. |
| `solution` | Markdown contenant du code complet commenté et une explication du raisonnement et des pièges. Jamais un champ `correction`. |

Varie progressivement la difficulté. Chaque exercice s'ancre dans Cuisine,
Finance ou Enduro selon `projets_cibles`, sans exemples abstraits.
Avec `["Tous"]`, répartis les six exercices entre les trois secteurs si le
chapitre en a six. Le code est en anglais (noms, docstrings, commentaires,
conventions PEP 8), le texte pédagogique en français.

Toute notion, fonction, méthode, syntaxe ou option employée dans la consigne,
les indices **ou la solution** doit être enseignée dans la théorie du chapitre
ou dans la théorie d'un chapitre antérieur. Les ressources sont un complément,
pas un substitut à l'introduction d'un prérequis. Sinon, simplifie l'exercice ou
fais compléter la théorie avant de terminer.

Fournis les données nécessaires dans la consigne. N'impose aucun service
externe ou fichier réel indisponible sans exemple de données de remplacement.
Les résultats attendus doivent être cohérents avec ces données ; relis-les
sans exécuter les blocs de code. Pas de promesse de rendement financier ni de
recommandation de santé tirée d'une formule pédagogique.

## Génération JSON obligatoire

N'écris pas manuellement du JSON avec de longs blocs Markdown échappés.
Crée un script Python temporaire d'édition contenant une liste de dictionnaires
Python et des chaînes multilignes pour les consignes/solutions, puis sérialise :

```python
import json
from pathlib import Path

# Set chapter_dir explicitly to the requested existing chapter directory.
# Build exercises as a list of dictionaries with the exact fields above.
output_path = chapter_dir / "exercices.json"
with output_path.open("w", encoding="utf-8") as output_file:
    json.dump(exercises, output_file, ensure_ascii=False, indent=2)
    output_file.write("\n")
```

Pour embarquer des docstrings `"""..."""` dans le code, utilise des chaînes
externes `r'''...'''` si approprié : le préfixe brut préserve les `\n` présents
dans le code à afficher, tout en conservant les vrais retours ligne du Markdown.
Le script ne doit faire qu'assembler et sérialiser du texte, jamais exécuter,
importer ou évaluer les exemples. Ne l'intègre pas au moteur ; supprime seulement
ce script temporaire à la fin. Ne laisse pas une seconde source permanente de
contenu généré.

Recharge le JSON avec `json.load`, contrôle ses clés, les types, les 4 à 6
exercices, les 2 à 3 indices et l'unicité des IDs ; compare les IDs avec le
relevé initial. La validation complète avec le modèle réel se fait via
`python -m agents.validate_chapter <cours> <slug>` après le projet.

## Limites

Écris uniquement les exercices du chapitre demandé (et le script temporaire).
Ne touche ni au moteur, ni aux modèles, ni à la base de progression.
N'ajoute aucun champ JSON. Ne lance ni les exemples, ni les solutions, ni le
code de l'apprenant : pas de notation automatique, d'exécution à distance ou
de sandbox. Le statut reste à la charge de l'orchestrateur après relecture.
Ne crée aucun commit et ne pousse rien.
