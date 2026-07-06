Tes scripts tiennent pour l'instant dans un fichier. Ce chapitre les fait passer à l'échelle : découpage en modules et packages, gestion d'erreurs digne de ce nom (fini le programme qui meurt sur une traceback), et typage vérifié par `mypy` — le filet de sécurité que tu connaissais avec le compilateur C++.

## 1. Modules

Un **module** = un fichier `.py`. Tout fichier Python est importable :

```python
# calculs.py
def zone_cardiaque(fc, fc_max):
    ...

# main.py
import calculs
calculs.zone_cardiaque(152, 185)

from calculs import zone_cardiaque      # importe UN nom dans l'espace courant
from calculs import zone_cardiaque as zc   # alias
```

Règles pratiques :

- `import module` garde le préfixe (`calculs.zone_cardiaque`) : plus verbeux mais on sait d'où vient chaque nom. `from ... import nom` pour les noms très utilisés.
- **Jamais** `from module import *` : pollue l'espace de noms, casse l'autocomplétion et mypy.
- Les imports vivent en tête de fichier, en trois groupes (stdlib / tiers / local) — PEP 8, chapitre 0.

À l'import, le fichier est **exécuté** une fois (définitions de fonctions, constantes...). C'est pour ça que le point d'entrée se protège :

```python
if __name__ == "__main__":     # vrai si exécuté directement, faux si importé
    main()
```

`__name__` vaut `"__main__"` à l'exécution directe, et `"calculs"` quand le module est importé. Sans cette garde, importer un module déclencherait son code de démonstration.

## 2. Packages

Un **package** = un dossier contenant `__init__.py` (souvent vide — il marque le dossier comme importable et s'exécute au premier import) :

```
recettes/
├── __init__.py
├── donnees.py        # les données et leur chargement
├── recherche.py      # la logique métier
├── exceptions.py     # les exceptions du package
└── cli.py            # l'interface
```

```python
from recettes.recherche import realisables      # import absolu : lisible, robuste
from .exceptions import RecetteInconnue         # import relatif : SEULEMENT
                                                # à l'intérieur du package
```

Préfère les **imports absolus** partout ; les relatifs (`.`, `..`) se justifient dans le code interne d'un package (c'est ce que fait `app/` de cette application : `from . import content, database`).

Exécuter un package : `python -m recettes` lance `recettes/__main__.py`. Le flag `-m` exécute *en tant que module*, ce qui rend les imports du package fiables quel que soit le dossier courant — habitude à prendre (`python -m pytest`, `python -m venv`, ...).

Découpage type d'une application : `donnees` (accès aux données), `metier`/`calculs` (logique pure, testable), `cli` ou `web` (présentation), `exceptions` (erreurs du domaine). C'est la séparation déjà pratiquée aux chapitres 1-2, officialisée par la structure de fichiers.

## 3. Exceptions

### La mécanique

```python
try:
    valeur = int(saisie)
    resultat = 100 / valeur
except ValueError:                      # int("abc")
    print("Entier attendu.")
except ZeroDivisionError as exc:        # l'objet exception est disponible
    print(f"Division impossible : {exc}")
except (TypeError, KeyError):           # plusieurs types d'un coup
    ...
else:
    print("Aucune erreur — s'exécute seulement si le try a réussi.")
finally:
    print("Toujours exécuté (nettoyage), erreur ou pas.")
```

Règles d'or :

- **Capture précis.** `except Exception` attrape tout, y compris les bugs que tu voudrais voir ; `except:` nu attrape même Ctrl+C. Les deux sont des interdits sauf tout en haut d'une application (dernier filet, avec journalisation).
- Le bloc `try` doit être **court** : uniquement les lignes susceptibles de lever.
- Une exception non capturée remonte la pile d'appels jusqu'à tuer le programme en affichant la **traceback** — lis-la de bas en haut : dernière ligne = le type et le message, au-dessus = le chemin d'appels.

### EAFP plutôt que LBYL

Le C vérifie avant d'agir (*Look Before You Leap*). Python préfère tenter et rattraper (*Easier to Ask Forgiveness than Permission*) :

```python
# LBYL — fragile (et si la clé disparaît entre le test et l'accès ?)
if "oeufs" in frigo and frigo["oeufs"] >= 3:
    frigo["oeufs"] -= 3

# EAFP — le cas nominal d'abord, l'erreur traitée à part
try:
    portions = int(saisie)
except ValueError:
    print("Entier attendu.")
```

Le `isdigit()` du chapitre 1 était un échafaudage pédagogique : la version idiomatique de `saisie_entier` utilise `try/except ValueError` (elle accepte au passage `"-3"` et `"  12  "`).

### Lever et créer ses exceptions

```python
class ErreurSeance(Exception):
    """Base des erreurs du domaine séance."""

class FcInvalide(ErreurSeance):
    pass

def valider_fc(fc):
    if not 40 <= fc <= 220:
        raise FcInvalide(f"FC hors limites physiologiques : {fc}")
```

- Une exception métier = une classe qui hérite d'`Exception` (souvent vide : le **type** porte le sens, le message porte le détail).
- Une **hiérarchie** permet à l'appelant de choisir sa granularité : `except FcInvalide` ou `except ErreurSeance` (attrape toutes les erreurs du domaine).
- Ré-emballer une erreur technique en erreur métier se fait avec le **chaînage** :

```python
def parser_duree(texte):
    try:
        h, m = texte.split(":")
        return int(h) * 60 + int(m)
    except ValueError as exc:
        raise FormatDureeInvalide(f"attendu 'h:mm', reçu {texte!r}") from exc
```

Le `from exc` conserve la cause d'origine dans la traceback (`The above exception was the direct cause...`) : l'appelant voit l'erreur métier, le débogueur voit tout.

## 4. Type hints

Python reste dynamique, mais les **annotations** documentent et permettent la vérification statique :

```python
def allure_min_km(distance_km: float, duree_min: int) -> tuple[int, int]:
    ...

def par_ingredient(recettes: list[dict[str, object]], ingredient: str) -> list[str]:
    ...

def trouver(recettes: list[Recette], nom: str) -> Recette | None:
    ...        # "| None" : peut ne rien trouver — l'appelant DOIT gérer ce cas
```

L'essentiel du vocabulaire :

| Annotation | Sens |
|---|---|
| `int`, `float`, `str`, `bool` | types simples |
| `list[float]`, `set[str]`, `dict[str, int]` | conteneurs paramétrés |
| `tuple[int, int]` / `tuple[str, ...]` | tuple fixe / longueur libre |
| `X | None` | optionnel (ex-`Optional[X]`) |
| `X | Y` | union (ex-`Union[X, Y]`) |
| `Callable[[int, str], bool]` | fonction passée en paramètre |
| `Any` | « je renonce à typer » — à éviter, il désactive la vérification |

Deux compléments utiles :

```python
from typing import TypeAlias

Recette: TypeAlias = dict[str, object]      # nomme un type structurel répété

from __future__ import annotations          # en tête de fichier : les annotations
                                             # ne sont plus évaluées à l'exécution
```

Les annotations n'ont **aucun effet à l'exécution** (sauf usages spéciaux : dataclasses, Pydantic — chapitre 14). Elles servent trois clients : le lecteur, Pylance (autocomplétion, erreurs en direct dans VS Code) et mypy.

## 5. mypy

```bash
pip install mypy
mypy recettes/            # analyse sans exécuter
mypy --strict recettes/   # mode exigeant : tout doit être annoté
```

Lecture des erreurs classiques :

```
error: Argument 1 to "zone_cardiaque" has incompatible type "str"; expected "int"
error: Item "None" of "Recette | None" has no attribute "__getitem__"
error: Function is missing a return type annotation
```

La deuxième est la plus précieuse : mypy **force** à gérer le cas `None` avant d'utiliser la valeur (`if recette is None: ...`) — toute une classe de bugs (`NoneType has no attribute`) disparaît à la compilation, comme un déréférencement de pointeur nul détecté statiquement.

Adoption pragmatique : typage **graduel**. Annote d'abord les signatures publiques (fonctions appelées depuis d'autres modules), lance `mypy` sans options, corrige, puis durcis vers `--strict` sur les nouveaux modules. Configuration dans `pyproject.toml` :

```toml
[tool.mypy]
python_version = "3.12"
strict = true
```

## Checklist de fin de chapitre

- [ ] Je découpe un programme en modules cohérents et je sais ce que fait réellement `import`.
- [ ] Je structure un package (`__init__.py`, `__main__.py`, imports absolus) et je le lance avec `python -m`.
- [ ] J'écris des `try/except` précis et courts, avec `else`/`finally` quand c'est pertinent.
- [ ] Je définis une hiérarchie d'exceptions métier et je chaîne avec `raise ... from`.
- [ ] Je préfère EAFP à la cascade de tests préalables.
- [ ] J'annote toutes mes signatures (conteneurs paramétrés, `| None`) et je fais passer mypy.
