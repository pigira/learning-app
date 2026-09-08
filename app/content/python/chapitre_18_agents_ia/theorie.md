Au chapitre 17, le modèle enchaînait des outils à ta demande. Un **agent** va plus loin : on lui confie une **mission** (« planifie une semaine de dîners avec ce que j'ai, mes allergies et 4 h de cuisine max »), et il décide seul de la séquence d'actions jusqu'à l'atteindre. Ce chapitre structure cette autonomie — boucle ReAct, mémoire de travail, contraintes vérifiées par le code, garde-fous — pour l'agent planificateur de repas de l'app Cuisine.

## 1. Du function calling à l'agent

La boucle du chapitre 17 était déjà agentique en germe. Ce qui fait la différence :

| Function calling (ch. 17) | Agent (ch. 18) |
|---|---|
| Répond à une question | Poursuit un objectif multi-étapes |
| L'utilisateur pilote le fil | L'agent planifie sa propre séquence |
| 1-3 appels d'outils | boucle jusqu'à « objectif atteint » |
| Sortie = une réponse | Sortie = un livrable structuré (un plan) |

La bascule se produit quand la tâche exige de **raisonner sur des résultats intermédiaires** pour décider de la suite : chercher les recettes réalisables → constater qu'il en manque → calculer les courses minimales → réévaluer sous la contrainte de budget. C'est un cycle, pas une ligne droite.

## 2. Le pattern ReAct : Reason + Act

ReAct structure chaque tour en trois temps : **Thought** (le modèle raisonne sur l'état et décide), **Action** (il appelle un outil), **Observation** (ton code renvoie le résultat). Répété jusqu'à la réponse finale.

```
Thought: il me faut d'abord savoir ce qui est réalisable avec le frigo.
Action: recettes_realisables()
Observation: ["omelette", "pâtes pesto"]
Thought: seulement 2 pour 7 dîners. Je cherche des recettes proches à faibles courses.
Action: recettes_a_faibles_courses(max_manquants=2)
Observation: [...]
Thought: j'ai de quoi composer 7 dîners variés. Je produis le plan.
Action: (réponse finale structurée)
```

En pratique avec le function calling : le « Thought » est le raisonnement interne du modèle (parfois visible si tu demandes un champ `reasoning`, sinon implicite), l'« Action » est un `tool_call`, l'« Observation » est ton message `role: tool`. Tu obtiens ReAct **gratuitement** avec la boucle du chapitre 17 — ce chapitre ajoute ce qu'il faut autour pour qu'elle soit fiable et cadrée.

Rendre la trace explicite (logger chaque Thought/Action/Observation) est non négociable : un agent est **indébogable** sans sa trace d'exécution.

## 3. Concevoir les outils d'un agent

Les outils sont l'interface de l'agent avec le monde — leur conception détermine tout :

- **Granularité juste** : ni trop fins (`get_recette_par_id` × 20 → l'agent se perd en micro-appels), ni trop gros (`fais_tout` → l'agent ne contrôle rien). Vise des outils qui correspondent à des étapes de raisonnement (« que puis-je cuisiner ? », « que manque-t-il ? », « combien ça coûte ? »).
- **Descriptions = spécifications** : quand utiliser l'outil, format exact des paramètres, forme du résultat, cas d'erreur. L'agent ne lit que ça.
- **Schémas d'entrée stricts** (Pydantic, chapitre 17) : le poste-frontière. L'agent propose, ton code valide et dispose.
- **Résultats compacts et informatifs** : assez pour raisonner, pas de quoi noyer le contexte (chapitre 17 §5). Une erreur structurée (`{"erreur": ..., "alternatives": [...]}`) vaut mieux qu'une exception — l'agent peut rebondir dessus.

## 4. Mémoire de travail

L'agent accumule un état au fil des tours. Deux niveaux :

- **Le contexte de conversation** (les `messages`) : la mémoire courte, portée par l'historique — mais elle grossit et coûte (compaction du chapitre 17).
- **Un état structuré côté code** : plutôt que de tout laisser dans le contexte, maintiens un objet `EtatPlanification` (recettes candidates, plan partiel, courses cumulées, contraintes restantes) que les outils lisent et mettent à jour. L'agent raisonne sur des **résumés** de cet état, pas sur des données brutes répétées.

Ce déport de l'état dans du code déterministe est la clé de la fiabilité : le calcul des courses, la vérification des allergies, le compte des portions ne dépendent PAS du modèle — ils sont exacts par construction.

## 5. Contraintes : dures vs souples

La distinction la plus importante du chapitre.

- **Contraintes dures** (allergies, régime, budget max) : elles ne peuvent JAMAIS être violées. Elles sont vérifiées **par ton code**, en aval des propositions de l'agent — jamais confiées au seul prompt. Un LLM qui « sait » qu'il ne faut pas d'arachide se trompera un jour ; un filtre `if arachide in ingredients: rejeter` ne se trompe jamais.
- **Contraintes souples** (préférences, variété, « plutôt léger le soir ») : elles guident, orientent, se négocient. Elles passent par le **system prompt** et le raisonnement de l'agent.

Le pattern : le prompt oriente (souple), le code garantit (dur). Concrètement, tout plan produit par l'agent traverse un `valider_plan(plan, profil) -> list[Violation]` déterministe ; si une contrainte dure est violée, on **rejette et on renvoie l'erreur à l'agent** (« la recette X contient de l'arachide, interdite — propose une autre »), on ne l'affiche jamais à l'utilisateur. La sécurité ne se délègue pas au modèle.

## 6. Garde-fous

Un agent autonome DOIT être borné — c'est une question de coût, de temps et de sûreté :

| Garde-fou | Pourquoi | Mise en œuvre |
|---|---|---|
| Nombre max de tours | éviter les boucles infinies | `for _ in range(max_tours)` + sortie propre |
| Budget de tokens | plafonner le coût | `SuiviUsage` du chapitre 17 |
| Validation des sorties | contraintes dures | `valider_plan` déterministe |
| Validation des arguments d'outils | entrées non fiables | Pydantic par outil |
| Détection de boucle | agent qui répète la même action | mémoriser les derniers appels, casser si répétition |
| Humain dans la boucle | actions irréversibles | pour tout ce qui engage (achat, envoi) : proposer, ne pas exécuter |

Le dernier point est une règle de conception : un agent **propose**, l'humain **dispose** pour toute action à conséquence. Planifier des repas et dresser une liste de courses : autonome. Passer commande : jamais sans validation explicite.

## 7. Évaluer un agent

Un agent n'est pas testable comme une fonction pure (sortie non déterministe). On l'évalue sur un **jeu de scénarios** avec des critères vérifiables par code :

```python
SCENARIOS = [
    {"frigo": [...], "profil": {"allergies": ["arachide"]},
     "verifier": lambda plan: aucune_arachide(plan) and len(plan) == 7},
    {"frigo": [], "profil": {...},
     "verifier": lambda plan: plan.liste_courses is not None},   # frigo vide → courses
]
```

On mesure le **taux de réussite** sur ces critères (contraintes dures respectées, objectif atteint, plan cohérent), pas la formulation exacte. Les critères de contraintes dures doivent réussir à **100 %** — c'est non négociable, et c'est pour ça qu'ils sont vérifiés par du code déterministe, pas par appréciation. Ce jeu de scénarios est un test de non-régression : à chaque modification du prompt ou des outils, on le rejoue.

## 8. Frameworks : pourquoi on s'en passe ici

LangChain, LlamaIndex, l'Agents SDK d'OpenAI... existent. Tu construis l'agent **à la main** dans ce parcours pour une raison : comprendre chaque rouage (boucle, état, contraintes, garde-fous) avant de laisser un framework les cacher. Une boucle ReAct maison fait ~150 lignes lisibles et débogables. Quand tu adopteras un framework, tu sauras ce qu'il fait — et ce qu'il ne fait pas à ta place (les contraintes dures resteront TON code).

## Checklist de fin de chapitre

- [ ] Je distingue function calling (répondre) et agent (poursuivre un objectif), et je sais quand la bascule s'impose.
- [ ] J'implémente une boucle ReAct tracée (Thought/Action/Observation) bornée.
- [ ] Je conçois des outils à la bonne granularité, avec état déporté dans du code déterministe.
- [ ] Je vérifie les contraintes DURES par du code en aval, jamais par le seul prompt.
- [ ] Je mets en place tous les garde-fous (tours, budget, validation, détection de boucle, humain dans la boucle).
- [ ] J'évalue l'agent sur un jeu de scénarios à critères vérifiables (100 % sur les contraintes dures).
