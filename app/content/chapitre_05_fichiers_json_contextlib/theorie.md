Jusqu'ici, tes données mouraient avec le programme. Ce chapitre les fait survivre : fichiers texte, JSON (le format d'échange universel — configs, API, sauvegardes), CSV, avec `pathlib` pour les chemins et les context managers pour ne jamais laisser une ressource ouverte.

## 1. Ouvrir un fichier : `open()` et `with`

```python
with open("data/seances.csv", encoding="utf-8") as f:
    contenu = f.read()
# ici le fichier est FERMÉ, quoi qu'il se soit passé dans le bloc
```

`with` garantit la fermeture même en cas d'exception — c'est le `RAII` du C++, en explicite. Un `open()` sans `with` est un bug en puissance (fichier verrouillé, écritures non flushées).

Les modes :

| Mode | Effet |
|---|---|
| `"r"` | lecture (défaut) — `FileNotFoundError` si absent |
| `"w"` | écriture — **écrase** le fichier existant |
| `"a"` | ajout en fin de fichier |
| `"x"` | création exclusive — erreur si le fichier existe |
| `"rb"` / `"wb"` | binaire (bytes) — chapitre 16 |

**Toujours** préciser `encoding="utf-8"` en mode texte : l'encodage par défaut dépend de la machine (piège classique de portabilité, même si macOS est déjà en UTF-8).

Lecture : `f.read()` (tout), `f.readlines()` (liste de lignes avec `\n`), ou — le plus idiomatique pour les gros fichiers — itérer directement :

```python
with open(chemin, encoding="utf-8") as f:
    for ligne in f:                  # une ligne à la fois, mémoire constante
        traiter(ligne.rstrip("\n"))
```

Écriture : `f.write(texte)` (pas de `\n` automatique), `print(texte, file=f)` (avec).

## 2. `pathlib` : les chemins en objets

Fini la concaténation de chaînes : `pathlib.Path` est le standard moderne.

```python
from pathlib import Path

base = Path("data")
chemin = base / "seances" / "2026-07.csv"    # l'opérateur / construit le chemin

chemin.exists()          # bool
chemin.suffix            # ".csv"
chemin.stem              # "2026-07"
chemin.name              # "2026-07.csv"
chemin.parent            # Path("data/seances")
chemin.parent.mkdir(parents=True, exist_ok=True)   # mkdir -p

Path.home()              # /Users/pierre
Path(__file__).parent    # le dossier DU SCRIPT (chemins robustes au cwd)
```

Raccourcis lecture/écriture qui gèrent open/close tout seuls :

```python
texte = chemin.read_text(encoding="utf-8")
chemin.write_text(texte, encoding="utf-8")
```

Et la découverte de fichiers, qui remplace les boucles de listing :

```python
for csv_file in sorted(Path("data").glob("*.csv")):      # data/IWDA.csv, ...
    ...
for f in Path("data").rglob("*.fit"):                    # récursif
    ...
```

Cette application fonctionne ainsi : `content.py` fait `CONTENT_DIR.iterdir()` et `(dossier / "chapitre.json").exists()` — relis-le, tout doit se comprendre maintenant.

## 3. JSON

JSON est le format pivot : configs, réponses d'API (chapitre 9), sauvegardes. Correspondance quasi directe avec Python :

| JSON | Python |
|---|---|
| `{}` objet | `dict` |
| `[]` | `list` |
| `"texte"` | `str` |
| `42` / `3.14` | `int` / `float` |
| `true` / `false` / `null` | `True` / `False` / `None` |

```python
import json

# Écrire
with open("portefeuille.json", "w", encoding="utf-8") as f:
    json.dump(donnees, f, ensure_ascii=False, indent=2)

# Lire
with open("portefeuille.json", encoding="utf-8") as f:
    donnees = json.load(f)

texte = json.dumps(donnees)      # -> str   (s = string)
donnees = json.loads(texte)      # str ->
```

- `ensure_ascii=False` : sans lui, `"crème"` devient `"crème"` dans le fichier.
- `indent=2` : lisible et diffable — toujours pour les fichiers destinés à des humains.

**Limites à connaître** : JSON ne connaît ni les dates, ni les sets, ni tes objets. `json.dump(seance)` sur une dataclass → `TypeError`. La solution est le pattern du chapitre 3 :

```python
json.dump(recette.to_dict(), f, ensure_ascii=False, indent=2)   # aller
recette = Recette.from_dict(json.load(f))                        # retour
```

Les dates voyagent en `str` ISO (`"2026-07-06"`) — encore une raison de ce format. Erreur à capturer en lecture : `json.JSONDecodeError` (fichier corrompu ou tronqué).

## 4. CSV

Le `split(",")` artisanal du chapitre 0 casse dès qu'un champ contient une virgule (`"pates, fraîches"`). Le module `csv` gère les guillemets, les échappements et les dialectes :

```python
import csv

# Lecture en dicts (l'en-tête fournit les clés)
with open("data/seances.csv", encoding="utf-8", newline="") as f:
    for ligne in csv.DictReader(f):
        # ligne = {"date": "2026-06-01", "sport": "course", "duree_min": "42", ...}
        duree = int(ligne["duree_min"])       # tout est str : convertir

# Écriture
with open("export.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "sport", "duree_min"])
    writer.writeheader()
    writer.writerows(seances)     # liste de dicts
```

Deux pièges : `newline=""` est requis par le module (gestion des fins de ligne), et **tout est `str`** en lecture — les conversions restent ta responsabilité (Pandas les automatisera au chapitre 10).

## 5. Context managers : le protocole derrière `with`

`with X() as x:` appelle `X.__enter__()` à l'entrée et `X.__exit__()` à la sortie — **toujours**, exception ou pas. Fichiers, connexions SQLite, verrous : même protocole partout.

Écrire le sien est trivial avec `contextlib` :

```python
import time
from contextlib import contextmanager

@contextmanager
def chrono(label: str):
    debut = time.perf_counter()
    try:
        yield                      # ← le bloc with s'exécute ici
    finally:
        duree = time.perf_counter() - debut
        print(f"[{label}] {duree:.3f} s")


with chrono("chargement des cours"):
    donnees = charger_cours()      # chronométré même si ça lève
```

Anatomie : tout ce qui précède `yield` = `__enter__` ; tout ce qui suit (dans le `finally`) = `__exit__`. Le `yield` peut fournir une valeur (`with chrono(...) as c:`). Cas d'usage typiques : chronométrage, connexion ouverte/fermée, dossier temporaire, transaction (le `with conn:` de `database.py` dans cette application en est un).

## 6. Erreurs de fichiers : le monde réel

Un programme qui lit des fichiers doit survivre à leur absence et à leur corruption — chapitre 4 appliqué :

```python
def charger_portefeuille(chemin: Path) -> list[dict]:
    try:
        texte = chemin.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []                          # premier lancement : cas NORMAL
    try:
        return json.loads(texte)
    except json.JSONDecodeError as exc:
        raise SauvegardeCorrompue(f"{chemin} illisible : {exc}") from exc
```

Distinction importante : le fichier **absent** est souvent un cas nominal (valeur par défaut), le fichier **corrompu** est toujours une erreur à remonter (écraser silencieusement la sauvegarde de l'utilisateur serait le pire comportement).

Pour l'écriture, le pattern **écriture atomique** évite le fichier à moitié écrit (crash, disque plein) :

```python
tmp = chemin.with_suffix(".tmp")
tmp.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
tmp.replace(chemin)      # renommage atomique : l'ancien fichier reste intact
                          # jusqu'à la dernière nanoseconde
```

## Checklist de fin de chapitre

- [ ] Je n'ouvre jamais un fichier sans `with`, ni sans `encoding="utf-8"`.
- [ ] Je construis tous mes chemins avec `pathlib` (`/`, `glob`, `mkdir(parents=True)`).
- [ ] Je sérialise en JSON (`ensure_ascii=False, indent=2`) via `to_dict`/`from_dict`.
- [ ] Je lis/écris le CSV avec `DictReader`/`DictWriter`, conversions de types comprises.
- [ ] Je sais écrire un context manager avec `@contextmanager` (yield dans un try/finally).
- [ ] Je distingue fichier absent (défaut) et fichier corrompu (exception métier chaînée), et j'écris de façon atomique.
