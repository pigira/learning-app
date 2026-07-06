Tu as vu la POO en C++ : classes, héritage, encapsulation. La version Python est plus légère — pas de headers, pas de visibilité stricte, pas de destructeurs à écrire — et ajoute deux outils très utilisés : les **propriétés** et les **dataclasses**. Objectif : modéliser proprement tes objets métier (Recette, Position, Séance).

## 1. Classes, `__init__`, `self`

```python
class Recette:
    def __init__(self, nom, temps_prep, temps_cuisson, portions=4):
        self.nom = nom                    # attributs créés à la volée
        self.temps_prep = temps_prep      # pas de déclaration préalable
        self.temps_cuisson = temps_cuisson
        self.portions = portions

    def temps_total(self):
        return self.temps_prep + self.temps_cuisson


r = Recette("Carbonara", 10, 15)     # pas de new
r.temps_total()                      # 25
```

- `__init__` est l'initialiseur (l'équivalent pratique du constructeur).
- `self` est le `this` du C++, mais **explicite** : premier paramètre de chaque méthode, fourni automatiquement à l'appel.
- Pas de `private`/`public` : tout est public. Convention : un préfixe `_` (`self._cache`) signale « interne, ne pas toucher » — c'est contractuel, pas imposé par le compilateur.

### Attributs de classe vs d'instance

```python
class Seance:
    SPORTS_VALIDES = ("course", "velo", "natation")   # attribut de CLASSE : partagé

    def __init__(self, sport):
        self.sport = sport                            # attribut d'INSTANCE
```

Piège : ne jamais utiliser un attribut de classe **mutable** (liste, dict) comme état d'instance — il serait partagé entre toutes les instances. L'état va dans `__init__`.

## 2. Méthodes dunder (double underscore)

Les méthodes `__xxx__` branchent tes objets sur la syntaxe du langage — l'équivalent de la surcharge d'opérateurs C++, en plus systématique.

```python
class Recette:
    ...
    def __repr__(self):
        # Représentation non ambiguë, pour le développeur (REPL, listes, debug)
        return f"Recette({self.nom!r}, {self.temps_total()} min)"

    def __eq__(self, autre):
        if not isinstance(autre, Recette):
            return NotImplemented
        return self.nom == autre.nom
```

| Dunder | Branche sur | Exemple |
|---|---|---|
| `__repr__` | `repr(x)`, affichage dans le REPL et les listes | debug |
| `__str__` | `str(x)`, `print(x)` (repli sur `__repr__` si absent) | affichage utilisateur |
| `__eq__` | `==` | comparer deux recettes |
| `__lt__` | `<` (et permet `sorted` sans `key`) | trier des séances |
| `__len__` | `len(x)` | nombre d'ingrédients du frigo |
| `__contains__` | `in` | `"oeufs" in frigo` |
| `__iter__` | `for ... in x` | parcourir un portefeuille |

Règle pratique : écris toujours `__repr__` (le debug devient lisible). Attention : définir `__eq__` rend l'objet non hashable par défaut (inutilisable dans un set/clé de dict) — assume-le ou vois `__hash__` plus tard.

## 3. Propriétés — attributs calculés et validés

En Python, **pas de getters/setters à la Java** : on expose les attributs. Le jour où un attribut doit devenir calculé ou validé, `@property` le fait **sans changer le code appelant** :

```python
class Position:
    def __init__(self, nom, quantite, pru, cours):
        self.nom = nom
        self.quantite = quantite
        self.pru = pru          # prix de revient unitaire
        self._cours = cours     # stockage interne

    @property
    def cours(self):
        return self._cours

    @cours.setter
    def cours(self, valeur):
        if valeur <= 0:
            raise ValueError(f"cours invalide : {valeur}")
        self._cours = valeur

    @property
    def valeur(self):               # attribut CALCULÉ, en lecture seule
        return self.quantite * self._cours

    @property
    def plus_value(self):
        return (self._cours - self.pru) * self.quantite


p = Position("IWDA", 50, 80.0, 92.5)
p.valeur          # 4625.0 — s'utilise comme un attribut, sans parenthèses
p.cours = 95.0    # passe par le setter (validation)
p.cours = -3      # ValueError
```

`raise ValueError(...)` lève une exception — mécanique détaillée au chapitre 4 ; ici, retiens que c'est la façon standard de refuser une valeur.

## 4. Héritage

```python
class Seance:
    def __init__(self, date, duree_min, fc_moy):
        self.date = date
        self.duree_min = duree_min
        self.fc_moy = fc_moy

    def resume(self):
        return f"{self.date} — {self.duree_min} min, FC moy {self.fc_moy}"


class SeanceCourse(Seance):
    def __init__(self, date, duree_min, fc_moy, distance_km):
        super().__init__(date, duree_min, fc_moy)   # initialise la partie parente
        self.distance_km = distance_km

    def resume(self):                               # override
        allure = self.duree_min / self.distance_km
        return super().resume() + f", {self.distance_km} km ({allure:.1f} min/km)"
```

- `super()` sans argument (pas de `Base::` à écrire).
- Le **polymorphisme est natif** : tout est virtuel, une boucle sur une liste mixte appelle la bonne méthode sans pointeur ni `virtual`.
- `isinstance(x, Seance)` teste le type (sous-classes incluses).

**Composition plutôt qu'héritage** : hérite pour une vraie relation « est un » avec comportement spécialisé (SeanceCourse *est une* Seance). Pour « possède un » (un Portefeuille *contient* des Positions), stocke l'objet en attribut. En cas de doute : composition. Les hiérarchies profondes sont un anti-pattern en Python.

## 5. Dataclasses — les classes de données sans boilerplate

La moitié des classes sont des porteurs de données : `__init__`, `__repr__`, `__eq__` mécaniques. `@dataclass` les génère depuis les annotations de champs :

```python
from dataclasses import dataclass, field, asdict

@dataclass
class Seance:
    date: str                      # ISO "2026-07-06" — champ obligatoire
    sport: str
    duree_min: int
    distance_km: float = 0.0       # valeur par défaut
    tags: list[str] = field(default_factory=list)   # défaut MUTABLE : factory obligatoire


s1 = Seance("2026-07-01", "course", 48, 9.2)
s2 = Seance("2026-07-01", "course", 48, 9.2)
s1 == s2              # True : __eq__ généré, champ à champ
print(s1)             # Seance(date='2026-07-01', sport='course', ...) : __repr__ généré
asdict(s1)            # {'date': '2026-07-01', ...} → export dict/JSON
```

Options utiles :

- `@dataclass(order=True)` : génère `<`, `<=`... en comparant les champs **dans l'ordre de déclaration** → mets le champ de tri en premier.
- `@dataclass(frozen=True)` : instances immuables (hashables → utilisables dans un set).
- Les annotations de type (`date: str`) sont ici **obligatoires** : c'est elles qui déclarent les champs. Elles ne sont pas vérifiées à l'exécution (chapitre 4 pour le typing sérieux).
- On peut ajouter des méthodes et des `@property` normalement dans une dataclass.

Quand l'utiliser ? Objet principalement porteur de données → dataclass. Logique riche, invariants complexes, état interne → classe manuelle. Simple sac de clés/valeurs jetable → dict.

## 6. `classmethod` et `staticmethod`

`@classmethod` reçoit la **classe** (`cls`) au lieu de l'instance — usage principal : les **constructeurs alternatifs** :

```python
@dataclass
class Recette:
    nom: str
    temps_prep: int
    temps_cuisson: int
    portions: int = 4

    @classmethod
    def from_dict(cls, data):
        return cls(**data)      # ** décompresse le dict en arguments nommés

    def to_dict(self):
        return asdict(self)


r = Recette.from_dict({"nom": "Risotto", "temps_prep": 15, "temps_cuisson": 30})
```

Pourquoi pas une fonction libre ? Parce que `cls` respecte l'héritage (une sous-classe construira une instance d'elle-même) et que le constructeur vit avec sa classe. `@staticmethod` : fonction rangée dans la classe, sans `self` ni `cls` — purement organisationnel, rare.

## 7. Récapitulatif de conception

| Situation | Outil |
|---|---|
| Porteur de données (recette, position, séance) | `@dataclass` |
| Attribut calculé ou validé | `@property` |
| Objet-conteneur métier (portefeuille, frigo) | classe + dunders (`__len__`, `__contains__`, `__iter__`) |
| Construction depuis un dict/JSON | `@classmethod from_dict` |
| Variante spécialisée d'un comportement | héritage + `super()` |
| « Possède un/des » | composition (attribut) |

## Checklist de fin de chapitre

- [ ] J'écris une classe avec `__init__`, méthodes et `__repr__` systématique.
- [ ] Je sais la différence attribut de classe / attribut d'instance et le piège du mutable partagé.
- [ ] J'expose des valeurs calculées/validées avec `@property` (+ setter).
- [ ] J'utilise l'héritage avec `super()` quand c'est un vrai « est un », la composition sinon.
- [ ] Je modélise mes données avec `@dataclass` (defaults, `field(default_factory=...)`, `order`, `frozen`).
- [ ] J'écris des constructeurs alternatifs avec `@classmethod` et `cls(**data)`.
