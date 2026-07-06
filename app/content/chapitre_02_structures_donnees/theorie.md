Les quatre structures natives (`list`, `tuple`, `dict`, `set`) remplacent 90 % de ce que tu ferais en C++ avec `vector`, `map`, `set` — sans templates ni gestion mémoire. Bien les choisir et les combiner est LA compétence Python de base : toutes tes données applicatives (recettes, cours d'ETF, séances) seront des assemblages de ces briques.

## 1. `list` — séquence ordonnée et mutable

```python
cours = [98.3, 99.1, 97.8, 100.2, 101.0]

cours[0]        # 98.3
cours[-1]       # 101.0  → indices négatifs : depuis la fin
len(cours)      # 5
cours.append(102.3)        # ajout en fin
cours.insert(0, 97.5)      # insertion (coûteux en tête, comme un vector)
cours.remove(97.8)         # supprime la première occurrence (par valeur)
dernier = cours.pop()      # retire et renvoie le dernier
cours.extend([103.0, 104.1])   # concatène une autre liste
101.0 in cours             # test d'appartenance (O(n) sur une liste)
```

Fonctions intégrées qui travaillent sur toute séquence : `sum`, `min`, `max`, `sorted`, `len`, `any`, `all`.

### Slicing

`liste[début:fin:pas]` — `début` inclus, `fin` **exclue** :

```python
cours = [98.3, 99.1, 97.8, 100.2, 101.0, 100.6, 102.3]

cours[1:4]      # [99.1, 97.8, 100.2]
cours[:3]       # les 3 premiers
cours[-5:]      # les 5 derniers
cours[::2]      # un élément sur deux
cours[::-1]     # copie inversée
```

Un slice renvoie toujours une **nouvelle liste** — `cours[:]` est d'ailleurs l'idiome de copie superficielle.

### Mutabilité et références — le piège n°1

Une variable Python est une **référence** vers un objet (pense pointeur intelligent, pas valeur) :

```python
a = [1, 2, 3]
b = a            # b référence LA MÊME liste
b.append(4)
a                # [1, 2, 3, 4]  ← surprise si on pense "copie"

c = a.copy()     # vraie copie (superficielle) ; a[:] ou list(a) équivalents
```

Pour des structures imbriquées (liste de listes), la copie superficielle partage les sous-objets ; `copy.deepcopy()` copie tout (rare en pratique — on y reviendra si besoin).

### Trier

```python
temps = [42, 95, 51, 40]
temps.sort()                  # trie EN PLACE (modifie, renvoie None)
tries = sorted(temps)         # renvoie une NOUVELLE liste triée
sorted(temps, reverse=True)   # décroissant
```

Le paramètre `key` prend une fonction appliquée à chaque élément pour produire la clé de tri — indispensable sur des données structurées :

```python
recettes = [
    {"nom": "carbonara", "temps": 25},
    {"nom": "risotto", "temps": 45},
    {"nom": "omelette", "temps": 10},
]
sorted(recettes, key=lambda r: r["temps"])            # par temps croissant
sorted(recettes, key=lambda r: (r["temps"], r["nom"]))  # clé composée (tuple)
max(recettes, key=lambda r: r["temps"])               # key marche aussi sur min/max
```

`lambda x: expr` est une fonction anonyme d'une expression — c'est tout ce qu'il faut savoir pour l'instant.

## 2. `tuple` — séquence immuable

```python
point = (48.85, 2.35)
lat, lon = point            # unpacking
a, b = b, a                 # échange sans variable temporaire
seul = (42,)                # tuple à 1 élément : la virgule fait le tuple
```

Usage : données hétérogènes de taille fixe (un couple, un enregistrement léger), retours multiples de fonctions, clés de dict (car immuable donc hashable). Si ça se modifie ou se parcourt, c'est une liste ; si c'est figé et positionnel, c'est un tuple.

## 3. `dict` — associations clé → valeur

L'équivalent de `std::unordered_map`, omniprésent en Python (les objets JSON, chapitre 5, sont des dicts). Accès O(1), ordre d'insertion préservé.

```python
frigo = {"oeufs": 6, "lait": 1, "tomates": 4}

frigo["oeufs"]              # 6 ; KeyError si absent
frigo.get("farine")         # None si absent (pas d'exception)
frigo.get("farine", 0)      # 0 par défaut → idéal pour les compteurs
frigo["beurre"] = 250       # ajout ou écrasement
del frigo["lait"]
frigo.pop("tomates")        # retire et renvoie la valeur
"oeufs" in frigo            # test sur les CLÉS, O(1)
```

Itération :

```python
for ingredient in frigo:                  # sur les clés
for qte in frigo.values():
for ingredient, qte in frigo.items():     # clé + valeur — le plus courant
```

Fusion (3.9+) : `stock_total = frigo | courses` (les clés de droite gagnent). Idiome d'accumulation :

```python
totaux = {}
for depense in depenses:
    cat = depense["categorie"]
    totaux[cat] = totaux.get(cat, 0) + depense["montant"]
```

## 4. `set` — ensemble non ordonné d'éléments uniques

```python
ingredients = {"pates", "oeufs", "parmesan", "lardons"}
frigo = {"oeufs", "lait", "parmesan", "beurre"}

"oeufs" in frigo               # O(1) — LA raison d'utiliser un set
ingredients & frigo            # intersection : {"oeufs", "parmesan"}
ingredients | frigo            # union
ingredients - frigo            # différence : ce qui manque au frigo
ingredients ^ frigo            # différence symétrique
ingredients <= frigo           # inclusion : "tout est dans le frigo ?"
ingredients.isdisjoint(frigo)  # aucun élément commun ?

set([1, 2, 2, 3, 1])           # {1, 2, 3} → déduplication d'une liste
```

Attention : `{}` crée un **dict** vide ; un set vide s'écrit `set()`.

## 5. Itération avancée

```python
for i, cours in enumerate(historique):        # indice + valeur
for veille, jour in zip(cours, cours[1:]):    # paires consécutives
for nom, qte in zip(noms, quantites):         # itération parallèle

any(s["duree"] > 60 for s in seances)   # au moins un ?
all(q > 0 for q in frigo.values())      # tous ?
```

## 6. Comprehensions

La syntaxe idiomatique pour **construire** une collection à partir d'une autre — remplace le motif « liste vide + boucle + append » :

```python
# List comprehension : [expression for élément in itérable if condition]
distances = [s["distance"] for s in seances]
longues = [s for s in seances if s["duree"] > 45]
allures = [s["duree"] / s["distance"] for s in seances if s["sport"] == "course"]

# Dict comprehension
par_nom = {r["nom"]: r["temps"] for r in recettes}

# Set comprehension
sports = {s["sport"] for s in seances}
```

Règles de lisibilité : une comprehension = une transformation simple. Si tu as besoin de plusieurs conditions imbriquées ou d'effets de bord, écris une boucle. Une comprehension trop maligne est une dette, pas un trophée.

Variante paresseuse (generator expression) : `sum(s["distance"] for s in seances)` — pas de liste intermédiaire, à connaître de vue.

## 7. Choisir sa structure

| Besoin | Structure |
|---|---|
| Séquence ordonnée à parcourir/modifier/trier | `list` |
| Enregistrement figé, retour multiple, clé composée | `tuple` |
| Association clé → valeur, compteurs, index par nom | `dict` |
| Unicité, appartenance rapide, opérations ensemblistes | `set` |

Les données réelles sont des **imbrications** : une liste de recettes = `list[dict]`, où chaque recette contient une `list` d'ingrédients ; un portefeuille = `dict[str, dict]`. Savoir naviguer là-dedans (`recettes[0]["ingredients"][2]`) est exactement ce que demandent les exercices.

## Checklist de fin de chapitre

- [ ] Je manipule les listes (méthodes, slicing, indices négatifs) sans réfléchir.
- [ ] Je sais pourquoi `b = a` ne copie pas, et comment copier vraiment.
- [ ] Je trie n'importe quoi avec `sorted(key=...)`, y compris en multi-critères.
- [ ] J'utilise `.get`, `.items` et l'idiome d'accumulation sur les dicts.
- [ ] Je pense « set » dès qu'il s'agit d'unicité ou d'intersection/différence.
- [ ] J'écris des comprehensions simples et lisibles (list, dict, set).
- [ ] Je choisis la bonne structure sans hésiter (tableau ci-dessus).
