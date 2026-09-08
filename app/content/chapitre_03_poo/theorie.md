Tu connais déjà la POO en C++ : classes, héritage, encapsulation. La version Python est plus légère — pas de header, pas de visibilité stricte imposée par le compilateur, pas de destructeur à écrire — et ajoute deux outils très utilisés au quotidien : les **propriétés** et les **dataclasses**. Objectif du chapitre : modéliser proprement tes objets métier (une recette, une position boursière, une séance d'entraînement) avec le même niveau de rigueur qu'en C++, mais avec beaucoup moins de code.

Convention pour tout ce chapitre : le code (noms, docstrings, commentaires) est en anglais, conformément aux conventions retenues ici ; les explications restent en français. Sauf indication contraire, les exemples reçoivent des chaînes et des nombres finis du type annoncé : la validation complète d'une entrée externe sera étudiée plus tard.

## 1. Classes, `__init__`, `self`

```python
class Recipe:
    def __init__(self, name, prep_min, cook_min, servings=4):
        self.name = name              # attributes are created on the fly
        self.prep_min = prep_min      # no prior declaration needed
        self.cook_min = cook_min
        self.servings = servings

    def total_time(self):
        return self.prep_min + self.cook_min


r = Recipe("Carbonara", 10, 15)   # no `new` keyword
r.total_time()                    # 25
```

- `__init__` est l'initialiseur (l'équivalent pratique du constructeur C++). Il ne renvoie rien (`return` sans valeur, ou pas de `return` du tout).
- `self` est le `this` du C++, mais **explicite** : premier paramètre de chaque méthode, fourni automatiquement par Python à l'appel (`r.total_time()` transmet `r` comme `self`).
- Pas de `private`/`public` : tout attribut est accessible. Convention : un préfixe `_` (`self._cache`) signale « détail interne, ne pas toucher depuis l'extérieur » — c'est un contrat entre développeurs, pas une barrière du langage.

### Attributs de classe et attributs d'instance

```python
class Workout:
    VALID_SPORTS = ("running", "cycling", "swimming")   # CLASS attribute: shared by all instances

    def __init__(self, sport):
        self.sport = sport                              # INSTANCE attribute: one per object
```

`VALID_SPORTS` est partagé par les instances (accessible via `Workout.VALID_SPORTS` ou `self.VALID_SPORTS`). **Piège** : ne pas utiliser un attribut de classe **mutable** (liste, dict) pour un état censé appartenir à chaque instance. Un appel comme `self.tags.append(...)` modifierait la liste partagée, tandis que `self.tags = [...]` créerait un attribut propre à cette instance, masquant celui de la classe. Initialise donc l'état individuel dans `__init__`.

**Corrige les invariants dès `__init__`**, pas après coup : si un objet ne doit jamais exister dans un état incohérent (quantité négative, cours nul), la validation doit avoir lieu pendant la construction — pas seulement lors d'une modification ultérieure. La section 4 (propriétés) et la section 6 (`__post_init__` des dataclasses) montrent comment faire.

## 2. Méthodes dunder (double underscore)

Les méthodes `__xxx__` (« dunder », *double underscore*) branchent tes objets sur la syntaxe native du langage — l'équivalent de la surcharge d'opérateurs C++, appliquée de façon systématique par l'interpréteur lui-même.

```python
class Recipe:
    def __init__(self, name, prep_min, cook_min, servings=4):
        self.name = name
        self.prep_min = prep_min
        self.cook_min = cook_min
        self.servings = servings

    def total_time(self):
        return self.prep_min + self.cook_min

    def __repr__(self):
        # Unambiguous representation, for developers (REPL, lists, debugging)
        return f"Recipe({self.name!r}, {self.total_time()} min)"

    def __eq__(self, other):
        if not isinstance(other, Recipe):
            return NotImplemented
        return self.name == other.name
```

| Dunder | Branche sur | Exemple d'usage |
|---|---|---|
| `__repr__` | `repr(x)`, affichage dans le REPL et dans les listes | debug |
| `__str__` | `str(x)`, `print(x)` (repli sur `__repr__` si absent) | affichage utilisateur |
| `__eq__` | `==` | comparer deux recettes |
| `__lt__` | `<` (et permet `sorted()` sans `key`) | trier des séances |
| `__len__` | `len(x)` | nombre d'ingrédients d'un frigo |
| `__contains__` | `in` | `"eggs" in fridge` |
| `__iter__` | `for ... in x` | parcourir un portefeuille (section 8) |

Trois nouveautés dans l'exemple ci-dessus, à connaître précisément :

- **`!r` dans une f-string** : `{self.name!r}` appelle `repr(self.name)` au lieu de `str(self.name)`. Pour une chaîne, `repr` ajoute les guillemets : `{self.name!r}` affiche `'Carbonara'` (avec quotes), là où `{self.name}` afficherait `Carbonara` (sans quotes, ambigu avec un nombre ou un mot-clé). Systématique dans `__repr__`.
- **`isinstance(other, Recipe)`** : teste si `other` est une instance de `Recipe` (ou d'une de ses sous-classes) — `isinstance(x, C)` est le test de type idiomatique en Python, préférable à `type(x) == C` car il respecte l'héritage (section 5).
- **`return NotImplemented`** : ce n'est ni `None` ni une erreur, c'est une valeur spéciale qui signifie « ma méthode ne prend pas en charge ce type ». Python peut alors essayer la méthode de l'autre opérande ; une sous-classe à droite peut même avoir priorité. Si aucune méthode ne prend la comparaison en charge, `==` revient au test d'identité `x is y` : deux objets distincts donnent `False`. Renvoyer directement `False` donnerait déjà une réponse définitive, sans laisser l'autre type proposer sa comparaison.

**Règle pratique** : écris toujours `__repr__` — le debug (et l'affichage d'une liste d'objets) devient lisible immédiatement.

### Hashabilité — ce que `__eq__` casse, et ses limites

Les instances d'une classe simple que tu définis, sans personnaliser `__eq__` ni `__hash__`, sont **hashables** : `hash(x)` fournit un entier cohérent avec leur égalité par identité. Cela ne concerne pas tous les objets Python : les listes et les dictionnaires ne sont pas hashables. Dès que tu définis `__eq__` dans ta classe sans définir aussi `__hash__`, Python désactive le hash par défaut : impossible d'utiliser l'objet comme clé de `dict` ou élément d'un `set` (`TypeError`). Le contrat impose que deux objets égaux aient le **même hash** ; une égalité par `name` ne serait plus compatible avec le hash par identité.

Si tu as besoin d'un `__hash__` personnalisé, base-le sur les champs utilisés par `__eq__` et garantis leur stabilité pendant la vie de l'objet. Le fait qu'une chaîne soit immuable ne suffit pas si l'attribut peut être réaffecté à une autre chaîne. Si le hash change après insertion dans un `set`, l'objet reste rangé selon l'ancien hash tandis qu'une recherche utilise le nouveau : `x in my_set` peut devenir `False` alors que l'objet s'y trouve encore. Les `@dataclass(frozen=True)` (section 6) aident à préserver cette stabilité, avec une limite importante pour les champs imbriqués.

## 3. Les décorateurs, en un paragraphe

Tu vas croiser `@property`, `@classmethod`, `@staticmethod` et `@dataclass` dans ce chapitre : ce sont des **décorateurs**. Un décorateur est une fonction qui prend une fonction (ou une classe) et en renvoie une version enrichie ; la syntaxe `@decorator` juste au-dessus d'un `def` (ou d'un `class`) est un raccourci pour `func = decorator(func)`. Tu n'as pas besoin d'écrire tes propres décorateurs pour ce chapitre (technique plus avancée) — seulement de savoir lire et utiliser ceux que Python et sa bibliothèque standard fournissent déjà.

## 4. Propriétés — attributs calculés et validés

En Python, **pas de getters/setters à la Java** : on expose directement les attributs (`position.value`, pas `position.getValue()`). Le jour où un attribut doit devenir calculé ou validé, `@property` le fait **sans changer le code appelant** :

```python
class Position:
    def __init__(self, name, quantity, avg_price, market_price):
        self.name = name
        self.quantity = quantity
        self.avg_price = avg_price       # average purchase price
        self.market_price = market_price  # goes through the setter below -> validated immediately

    @property
    def market_price(self):
        return self._market_price

    @market_price.setter
    def market_price(self, value):
        if value <= 0:
            raise ValueError(f"invalid market price: {value}")
        self._market_price = value

    @property
    def value(self):                     # read-only computed attribute
        return self.quantity * self._market_price

    @property
    def unrealized_gain_eur(self):
        return (self._market_price - self.avg_price) * self.quantity


p = Position("IWDA", 50, 80.0, 92.5)
p.value              # 4625.0 -- used like a plain attribute, no parentheses
p.market_price = 95.0    # goes through the setter (validated)
p.market_price = -3      # raises ValueError
```

Points clés :

- Ordre des décorateurs : d'abord `@property` sur le getter (`def market_price(self):`), puis `@market_price.setter` sur une **deuxième** fonction du même nom, qui reçoit la valeur affectée.
- **Invariant du cours dès `__init__`** : `self.market_price = market_price` passe déjà par le setter. Celui-ci garantit un cours strictement positif à la création comme lors d'une modification par l'interface publique. Il ne valide pas automatiquement les autres champs ; l'exercice ajoute les contrôles de quantité et de prix de revient. Écrire directement dans `_market_price` contournerait cette protection.
- `raise ValueError(...)` **lève une exception** : l'exécution de la fonction s'arrête immédiatement à cet endroit et l'erreur remonte l'appelant. Ce chapitre se contente de lever l'exception pour signaler une valeur refusée ; **attraper** proprement une exception avec `try/except` est le sujet du chapitre 4. En attendant, si personne n'intercepte l'exception, le programme s'arrête et affiche une trace d'erreur (*traceback*) — c'est le comportement normal et attendu quand tu testes volontairement une valeur invalide dans ce chapitre.
- Complément de format (chapitre 1) : pour une plus-value qui peut être positive ou négative, le drapeau `+` dans une f-string (`{gain:+.1f}`) force l'affichage du signe même quand la valeur est positive — `+15.6` plutôt que `15.6`, symétrique de `-5.6`. Il se combine avec les autres options déjà vues : `{amount:+,.2f}` ajoute en plus le séparateur de milliers.

## 5. Héritage

```python
class Workout:
    def __init__(self, date, duration_min, avg_heart_rate):
        self.date = date
        self.duration_min = duration_min
        self.avg_heart_rate = avg_heart_rate

    def summary(self):
        return f"{self.date} -- {self.duration_min} min, avg HR {self.avg_heart_rate}"


class RunningWorkout(Workout):
    def __init__(self, date, duration_min, avg_heart_rate, distance_km):
        super().__init__(date, duration_min, avg_heart_rate)   # let the parent init its own part
        self.distance_km = distance_km

    def summary(self):                                          # override
        pace = self.duration_min / self.distance_km
        return super().summary() + f", {self.distance_km} km ({pace:.1f} min/km)"
```

- `super()` s'appelle sans argument (pas de `Base::` à écrire comme en C++).
- Le **polymorphisme est natif** : toute méthode est redéfinissable, la résolution est dynamique. Une boucle `for w in workouts: print(w.summary())` sur une liste d'objets de types différents appelle automatiquement la bonne version — pas de `virtual`, pas de pointeur.
- `isinstance(w, Workout)` teste le type **en incluant les sous-classes** : une `RunningWorkout` est aussi une `Workout`. C'est différent de `type(w) is Workout`, qui exclurait les sous-classes.

**Composition plutôt qu'héritage** : hérite pour une vraie relation « est un » avec un comportement spécialisé (`RunningWorkout` *est un* `Workout`). Pour une relation « possède un/des » (un portefeuille *contient* des positions), stocke l'objet en attribut au lieu d'hériter. En cas de doute, préfère la composition : les hiérarchies de classes profondes sont un anti-pattern courant en Python.

## 6. Dataclasses — les classes de données sans code répétitif

La moitié des classes qu'on écrit sont de simples porteurs de données : `__init__`, `__repr__`, `__eq__` mécaniques, sans logique. `@dataclass` génère tout cela depuis des **annotations de champs**.

### Un aperçu ciblé de `import`

`@dataclass` vit dans la bibliothèque standard, dans le module `dataclasses` : il faut donc l'importer. Le système complet des modules (créer les siens, les organiser en paquets) est le sujet du chapitre 4 ; retiens ici seulement le motif dont tu as besoin pour ce chapitre :

```python
from dataclasses import dataclass, field, asdict
```

`from nom_du_module import nom1, nom2` rend `nom1` et `nom2` directement utilisables dans ton fichier — pas de `#include`, pas de header, pas d'étape de link : l'interpréteur charge le module et te donne accès à ce que tu as listé.

### Déclarer les champs

```python
from dataclasses import dataclass, field


@dataclass
class TrainingSession:
    date: str                       # ISO "2026-07-06" -- required field
    sport: str
    duration_min: int
    distance_km: float = 0.0        # field with a default value
    heart_rate: int | None = None   # "int or nothing" -- union type hint
    tags: list[str] = field(default_factory=list)   # mutable default -> factory required

    def __post_init__(self):
        if self.duration_min <= 0:
            raise ValueError(f"duration_min must be positive: {self.duration_min}")


s1 = TrainingSession("2026-07-01", "running", 48, 9.2)
s2 = TrainingSession("2026-07-01", "running", 48, 9.2)
s1 == s2              # True -- __eq__ generated, field by field
print(s1)             # TrainingSession(date='2026-07-01', sport='running', ...) -- __repr__ generated
```

Nouveautés à bien comprendre :

- **Les annotations de type (`date: str`, `duration_min: int`) déclarent les champs** : c'est grâce à elles que `@dataclass` sait quoi mettre dans `__init__`. Elles ne sont **pas vérifiées à l'exécution** — écrire `TrainingSession(date=42, ...)` ne provoque aucune erreur immédiate, l'annotation est une documentation pour toi et les outils, pas un garde-fou automatique (le typing sérieux, avec des vérificateurs, arrive au chapitre 4).
- **`int | None`** est la syntaxe d'union de types (Python ≥ 3.10, disponible dans ce projet) : elle se lit « un `int`, ou bien `None` ». `list[str]` annonce « une liste de chaînes ».
- **`field(default_factory=list)`** : un défaut mutable (`tags: list[str] = []`) est refusé par Python à la déclaration d'une dataclass — même piège qu'un paramètre par défaut mutable dans une fonction (chapitre 1). `default_factory` fournit une fonction (ici `list`, appelée sans argument) qui **fabrique une valeur neuve à chaque instance**, au lieu d'un objet unique partagé.
- **`__post_init__`** : cette méthode est appelée par le `__init__` généré après l'affectation des champs. Elle permet de **refuser une construction invalide** : `TrainingSession(..., duration_min=-5)` lève immédiatement `ValueError`. Contrairement à un setter, elle n'est pas rappelée lors d'une affectation ultérieure : `session.duration_min = -5` resterait possible sur cette dataclass mutable. Pour conserver l'invariant, utilise une interface contrôlée ou des objets `frozen` reconstruits lorsque leurs données changent.

### `order=True` et `frozen=True`

```python
@dataclass(order=True)
class TrainingSession:
    date: str          # comparisons use fields IN DECLARATION ORDER: date compared first
    sport: str
    duration_min: int
```

`order=True` génère `<`, `<=`, `>`, `>=` en comparant les champs **dans l'ordre où ils sont déclarés**, comme un tuple : place donc le champ de tri en premier (ici `date`, une date ISO `AAAA-MM-JJ` se compare lexicographiquement comme chronologiquement). En cas d'égalité, les champs suivants départagent les objets. Ils doivent donc être comparables : `None` et un entier ne peuvent pas être ordonnés. Si seul le jour doit décider du tri, utilise plutôt `sorted(sessions, key=lambda session: session.date)`, déjà vu au chapitre 2.

```python
@dataclass(frozen=True)
class Waypoint:
    latitude: float
    longitude: float
    tags: list[str] = field(default_factory=list)


w = Waypoint(45.18, 5.72, tags=["summit"])
w.tags.append("checkpoint")   # works! the list itself is still mutable
# Try this assignment separately: it raises dataclasses.FrozenInstanceError.
# w.latitude = 0.0
```

**`frozen=True` n'est pas une immutabilité profonde** : il bloque uniquement la *réaffectation* d'un attribut (`w.latitude = 0.0`). Si un champ est un objet mutable (liste, dict), son **contenu** reste modifiable à travers ce champ (`w.tags.append(...)` fonctionne très bien). « Frozen » veut dire « les liens attribut → objet sont figés », pas « tout ce qui est atteignable depuis l'objet est figé ».

Corollaire sur le hash (voir section 2) : une dataclass `frozen=True` (avec `eq=True`, la valeur par défaut) génère un `__hash__` basé sur ses champs. Mais `hash(w)` lève `TypeError: unhashable type: 'list'` : le hash généré délègue à chaque champ, et `tags` est une liste. Il faut des champs hashables dont la valeur reste stable, pas seulement des attributs non réaffectables. Un tuple convient uniquement si chacun de ses éléments convient aussi ; un tuple contenant une liste n'est pas hashable.

Enfin : `asdict(instance)` (importé de `dataclasses`) exporte les champs en `dict` ordinaire, en parcourant les dataclasses et collections imbriquées et en copiant leurs données. Une liste exportée ne partage donc pas son contenu avec le champ source. C'est utile pour préparer un export JSON (chapitre 5), mais ce n'est pas encore une chaîne JSON. On peut ajouter des méthodes et des `@property` calculées normalement dans une dataclass.

Quand l'utiliser ? Objet principalement porteur de données (avec éventuellement des propriétés calculées et un `__post_init__` de validation) → dataclass. Logique riche, beaucoup d'invariants et de comportement → classe manuelle. Sac de clés/valeurs jetable, sans nom de champs stable → `dict` (chapitre 2).

## 7. `classmethod` et `staticmethod` — constructeurs alternatifs

`@classmethod` reçoit la **classe** (conventionnellement nommée `cls`) au lieu de l'instance — usage principal : les constructeurs alternatifs.

```python
from dataclasses import asdict, dataclass


@dataclass
class Recipe:
    name: str
    prep_min: int
    cook_min: int
    servings: int = 4

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)      # ** unpacks the dict into keyword arguments

    @staticmethod
    def is_valid_name(name):
        return bool(name.strip())


r = Recipe.from_dict({"name": "Risotto", "prep_min": 15, "cook_min": 30})
```

- **`**data`** dans `cls(**data)` décompresse un dict en arguments nommés : `{"name": "Risotto", "prep_min": 15, ...}` devient l'appel `cls(name="Risotto", prep_min=15, ...)`. C'est l'inverse de la construction d'un dict `{"name": ...}`.
- Pourquoi `@classmethod` plutôt qu'une fonction libre qui construit directement `Recipe` ? `cls` désigne la classe appelée : une sous-classe peut donc réutiliser le constructeur alternatif, à condition que ses arguments restent compatibles. Une fonction libre pourrait aussi accepter une classe en paramètre, mais la méthode lie cette opération à son modèle et se découvre via `Recipe.`.
- `@staticmethod` : une fonction simplement rangée dans l'espace de noms de la classe, sans `self` ni `cls` — purement organisationnel, utile pour un utilitaire lié au concept mais qui n'a besoin ni de l'instance ni de la classe.

## 8. Se comporter comme un conteneur natif

Une classe qui encapsule une collection interne peut s'intégrer aux idiomes Python vus au chapitre 2, via les dunders déjà présentés :

```python
class Fridge:
    def __init__(self):
        self._items = {}          # ingredient name -> quantity

    def add(self, name, qty):
        if qty <= 0:
            raise ValueError("quantity must be positive")
        self._items[name] = self._items.get(name, 0) + qty

    def remove(self, name, qty):
        if qty <= 0:
            raise ValueError("quantity must be positive")
        available = self._items.get(name, 0)
        if available < qty:
            raise ValueError(f"cannot remove {qty} {name}: only {available} available")
        self._items[name] = available - qty
        if self._items[name] == 0:
            del self._items[name]

    def __contains__(self, name):
        return name in self._items

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return f"Fridge({len(self)} items)"
```

`"eggs" in fridge` se lit comme la question posée, au lieu de `fridge.contains("eggs")` ; `len(fridge)` s'utilise comme sur une liste ou un dict natif. En passant par ces méthodes et avec les entrées numériques finies convenues, les quantités restent strictement positives et les clés épuisées disparaissent. Les contrôles ont lieu avant la mutation : une opération refusée laisse le stock inchangé.

Pour rendre un objet-conteneur itérable avec `for x in my_object`, implémente `__iter__` : le plus simple, quand ton objet enveloppe déjà une collection interne, est de **déléguer** à la fonction native `iter()`, qui prend n'importe quel itérable (liste, tuple, dict...) et renvoie son itérateur :

```python
class Portfolio:
    def __init__(self):
        self._positions = []

    def add(self, position):
        self._positions.append(position)

    def __len__(self):
        return len(self._positions)

    def __iter__(self):
        return iter(self._positions)   # delegate to the list's own iterator
```

Une fois `__iter__` défini, `for position in portfolio`, `sum(p.value for p in portfolio)`, `max(portfolio, key=...)` fonctionnent exactement comme sur une liste — c'est le même contrat que les conteneurs natifs, sans rien réécrire de plus. Composition, encore : le `Portfolio` *contient* des `Position`, il n'en hérite pas.

## 9. Récapitulatif de conception

| Situation | Outil |
|---|---|
| Porteur de données (recette, position, séance) | `@dataclass` (+ `__post_init__` si des invariants existent) |
| Attribut calculé ou validé | `@property` (+ setter si modifiable) |
| Objet-conteneur métier (portefeuille, frigo) | classe + dunders (`__len__`, `__contains__`, `__iter__`) |
| Construction depuis un dict (futur JSON) | `@classmethod from_dict` |
| Variante spécialisée d'un comportement (« est un ») | héritage + `super()` |
| « Possède un/des » | composition (attribut) |

## Checklist de fin de chapitre

- [ ] J'écris une classe avec `__init__`, des méthodes et un `__repr__` systématique (avec `!r` pour les champs texte).
- [ ] Je connais la différence attribut de classe / attribut d'instance, et le piège du mutable partagé.
- [ ] Je sais ce qu'est un décorateur (`@...`) sans avoir besoin d'en écrire un.
- [ ] Je valide un invariant dès `__init__` (via un setter de propriété, ou `__post_init__` pour une dataclass), pas après coup.
- [ ] J'expose des valeurs calculées/validées avec `@property` (+ setter), et je sais lever `ValueError` pour refuser une valeur invalide.
- [ ] Je sais pourquoi `__eq__` renvoie `NotImplemented` (pas `False`) face à un type inconnu, testé avec `isinstance`.
- [ ] Je sais pourquoi définir `__eq__` rend un objet non hashable, et pourquoi le hash ne doit jamais porter sur un champ mutable.
- [ ] J'utilise l'héritage avec `super()` pour un vrai « est un », la composition sinon.
- [ ] Je modélise mes données avec `@dataclass` (`field(default_factory=...)`, `order=True`, `frozen=True`) en sachant que `frozen` ne rend pas les champs mutables imbriqués immuables.
- [ ] J'écris des constructeurs alternatifs avec `@classmethod` et `cls(**data)`.
- [ ] Je rends un objet-conteneur idiomatique avec `__len__`, `__contains__`, et `__iter__` (délégué à `iter(...)`).
