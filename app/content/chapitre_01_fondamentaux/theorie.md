Tu connais déjà l'algorithmique en C/C++ : ce chapitre est une **translation**. On va droit à la syntaxe Python et aux différences qui piègent les habitués du C — pas de ré-explication de ce qu'est une boucle.

## 1. Exécution

Python est interprété : pas de compilation, pas de `main()` obligatoire. Le fichier est exécuté de haut en bas.

```bash
python3 script.py
```

Le REPL (`python3` seul) sert de calculatrice/laboratoire : tape une expression, elle s'évalue. Réflexe utile pour tester une syntaxe avant de l'écrire dans un fichier.

## 2. Variables et types

Typage **dynamique** (le type est porté par la valeur, pas par la variable) mais **fort** (pas de conversion implicite douteuse) :

```python
x = 3          # int
x = "trois"    # légal : la variable est ré-étiquetée
"3" + 4        # TypeError : pas de conversion implicite (contrairement à JS)
```

Types de base :

| Type | Exemples | Notes |
|---|---|---|
| `int` | `42`, `10_000_000` | **précision arbitraire** : pas d'overflow, pas de int32/int64 |
| `float` | `3.14`, `2e-3` | flottant IEEE 754 double — `0.1 + 0.2 != 0.3`, comme en C |
| `bool` | `True`, `False` | majuscule initiale ; sous-type de `int` |
| `str` | `"texte"`, `'texte'` | immuable, Unicode natif |
| `NoneType` | `None` | l'équivalent conceptuel de « pas de valeur » (≠ `NULL` pointeur) |

```python
type(3.14)       # <class 'float'>
int("42")        # conversions explicites : int(), float(), str()
int(3.9)         # 3 (troncature vers zéro)
round(3.9)       # 4
```

Pas de déclaration, pas de `const` : une constante est une convention de nommage, `TAUX_TVA = 0.055`.

## 3. Chaînes et f-strings

Les chaînes sont **immuables** : toute « modification » crée une nouvelle chaîne.

```python
nom = "carbonara"
nom.upper()          # "CARBONARA" (nom n'a pas changé)
"  x  ".strip()      # "x"
"a,b,c".split(",")   # ['a', 'b', 'c']
"-".join(["a", "b"]) # "a-b"
nom.replace("a", "o")
nom.startswith("carb")   # True
len(nom)             # 9
```

Le formatage moderne, c'est la **f-string** — ton `printf`, en mieux :

```python
prix = 12.5
qte = 3
print(f"Total : {prix * qte:.2f} €")     # expressions arbitraires + format
print(f"{qte:03d}")                      # 003  (zéro-padding)
print(f"{0.847:.1%}")                    # 84.7% (format pourcentage)
print(f"{'Vitesse':<12}: {28.4:>8.2f}")  # alignement gauche/droite
print(f"{prix=}")                        # prix=12.5 (debug rapide)
```

Chaîne multiligne : triple guillemets `"""..."""`.

## 4. Opérateurs — les pièges venant du C

```python
7 / 2      # 3.5   → la division / renvoie TOUJOURS un float
7 // 2     # 3     → division entière (floor), l'équivalent du / entier de C
-7 // 2    # -4    → floor, pas troncature vers zéro comme en C !
7 % 2      # 1     → le signe suit le DIVISEUR : -7 % 2 == 1 (≠ C)
2 ** 10    # 1024  → puissance
x += 1     # pas de x++ ni ++x en Python
```

Logique et comparaisons :

```python
a and b        # && ; a or b → || ; not a → !
0 < x < 10     # comparaisons chaînées : équivalent de (0 < x) && (x < 10)
x == y         # égalité de VALEUR
x is None      # identité d'objet — réservé en pratique aux tests None
```

**Truthiness** : dans un contexte booléen, sont faux `0`, `0.0`, `""`, `[]`, `{}`, `set()`, `None`. Tout le reste est vrai.

```python
if panier:              # idiomatique : "si le panier n'est pas vide"
    ...
```

`and`/`or` court-circuitent et renvoient l'un des opérandes (pas forcément un bool) : `nom = saisie or "défaut"` est un idiome courant.

## 5. Contrôle de flux

**L'indentation délimite les blocs.** Pas d'accolades : le `:` ouvre un bloc, l'indentation (4 espaces) le contient. C'est syntaxique, pas cosmétique.

```python
if fc >= 0.9 * fc_max:
    zone = 5
elif fc >= 0.8 * fc_max:      # elif, pas "else if"
    zone = 4
else:
    zone = 3

etat = "dur" if zone >= 4 else "facile"   # ternaire : x if cond else y
```

### Boucles

`while` est identique au C (il n'y a **pas** de `do...while`) :

```python
annees = 0
while capital < 100_000:
    capital *= 1.06
    annees += 1
```

`for` n'est **pas** le `for(;;)` du C : c'est un *for-each* qui itère sur un itérable.

```python
for cours in [98.3, 99.1, 100.2]:   # sur les éléments directement
    print(cours)

for i in range(5):          # 0,1,2,3,4     — l'équivalent de for(i=0;i<5;i++)
for i in range(1, 6):       # 1,2,3,4,5
for i in range(10, 0, -2):  # 10,8,6,4,2

for i, cours in enumerate([98.3, 99.1]):   # indice ET valeur quand nécessaire
    print(i, cours)
```

Règle de style : si tu écris `for i in range(len(liste))` pour faire `liste[i]`, itère plutôt directement sur les éléments (ou `enumerate`). `break` et `continue` fonctionnent comme en C.

### match/case (Python ≥ 3.10)

Le `switch` de Python, en plus puissant : il **déstructure** (pattern matching) et ne « tombe » pas d'un cas à l'autre (pas de fallthrough, pas de `break`).

```python
commande = "ajouter 3 tomates".split()

match commande:
    case ["quitter"]:
        print("au revoir")
    case ["ajouter", qte, produit] if qte.isdigit():   # garde
        print(f"+{qte} {produit}")
    case ["retirer", qte, produit]:
        print(f"-{qte} {produit}")
    case _:                                            # défaut
        print("commande inconnue")
```

## 6. Fonctions

```python
def allure(distance_km, temps_min):
    """Allure en min/km (docstring : documentation de la fonction)."""
    return temps_min / distance_km
```

- Pas de type de retour déclaré, pas de prototype, pas de surcharge. Une fonction sans `return` renvoie `None`.
- **Retours multiples** via un tuple, avec déballage à l'appel :

```python
def stats(valeurs):
    return min(valeurs), max(valeurs)

mini, maxi = stats([3, 8, 5])
```

- **Arguments par défaut** et **appel par mot-clé** (remplacent la surcharge) :

```python
def cups_vers_ml(cups, taille_cup=240.0):
    return cups * taille_cup

cups_vers_ml(1.5)                   # 360.0
cups_vers_ml(1.5, taille_cup=250)   # appel nommé : lisible et sans ambiguïté
```

**Piège classique** : ne jamais mettre un objet mutable en valeur par défaut (`def f(x, acc=[])`) — la liste est créée une seule fois et partagée entre les appels. Idiome correct : `acc=None` puis `if acc is None: acc = []`.

- `*args` / `**kwargs` : paramètres variadiques (tuple / dict). À savoir lire dès maintenant ; on s'en servira plus tard.

```python
def somme(*valeurs):        # somme(1, 2, 3)
    return sum(valeurs)
```

- **Portée** : une variable assignée dans une fonction est locale. Lire une globale est possible, la réassigner exige `global` — c'est presque toujours un signal de mauvais design : préfère paramètres et valeurs de retour.

### Le point d'entrée idiomatique

```python
def main():
    ...

if __name__ == "__main__":   # vrai seulement si le fichier est exécuté directement
    main()                   # (pas s'il est importé) — l'équivalent culturel du main() C
```

## 7. Table de translation C/C++ → Python

| C / C++ | Python |
|---|---|
| `printf("%d\n", x);` | `print(f"{x}")` |
| `int x = 3;` | `x = 3` |
| `x++;` / `--x;` | `x += 1` / `x -= 1` |
| `a && b`, `a \|\| b`, `!a` | `a and b`, `a or b`, `not a` |
| `7 / 2 == 3` (ints) | `7 // 2 == 3` (`/` donne 3.5) |
| `for (int i = 0; i < n; i++)` | `for i in range(n):` |
| `while (cond) { }` | `while cond:` |
| `do { } while (cond);` | n'existe pas → `while True:` + `break` |
| `switch/case` + `break` | `match/case` (sans fallthrough) |
| `NULL` / `nullptr` | `None` (tester avec `is None`) |
| `true` / `false` | `True` / `False` |
| `// commentaire` | `# commentaire` |
| `const double TVA = 0.055;` | `TAUX_TVA = 0.055` (convention) |
| `int main() { }` | `if __name__ == "__main__":` |
| pointeurs, `malloc`/`free` | n'existent pas : gestion mémoire automatique |
| fichiers `.h`, prototypes | n'existent pas : `import` (chapitre 4) |

## Checklist de fin de chapitre

- [ ] Je connais les 5 types de base et les conversions explicites.
- [ ] Je formate n'importe quelle sortie avec une f-string (`:.2f`, `:02d`, `:.0%`, alignement).
- [ ] Je ne confonds plus `/` et `//`, ni `==` et `is`.
- [ ] J'écris des `for` sur les éléments (pas sur les indices) et je sais quand `enumerate` s'impose.
- [ ] J'utilise `match/case` pour les aiguillages structurés.
- [ ] J'écris des fonctions avec valeurs par défaut, appels nommés et retours multiples.
- [ ] Mes scripts se terminent par le bloc `if __name__ == "__main__":`.
