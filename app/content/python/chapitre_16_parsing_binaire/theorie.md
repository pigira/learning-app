Ta montre Garmin enregistre chaque séance dans un fichier `.fit` : un format **binaire** compact, illisible avec un éditeur de texte. Ce chapitre ouvre cette boîte noire — d'abord les fondamentaux du binaire (`bytes`, `struct`), puis la librairie `fitparse` qui décode le format FIT et alimente tes DataFrames Enduro. C'est la brique d'ingestion manquante de ton projet sportif.

## 1. bytes vs str

Un fichier texte est une suite de caractères ; un fichier binaire, une suite d'**octets** (0-255). En Python, deux types distincts :

```python
texte = "séance"                 # str : des caractères (abstraction)
octets = texte.encode("utf-8")   # bytes : b'\\x73\\xc3\\xa9ance' — la représentation réelle
octets.decode("utf-8")           # retour au str

b"\\x00\\x2a"                     # littéral bytes : 2 octets (0 et 42)
octets[0]                        # 115 : indexer des bytes donne un INT
octets.hex(" ")                  # "73 c3 a9 61 6e 63 65" : dump hexadécimal lisible
```

Ouvrir un binaire : le mode `"rb"` (read binary) — pas d'`encoding`, on lit des octets bruts :

```python
from pathlib import Path
donnees = Path("seance.fit").read_bytes()      # bytes
print(donnees[:12].hex(" "))                    # les 12 premiers octets
```

L'hexadécimal est la langue du binaire : deux chiffres hex = un octet, `0x00` à `0xFF` = 0 à 255. `bytes.hex(" ")` est ton premier outil d'inspection.

## 2. struct : décoder des champs

Un format binaire range ses champs à des **positions** fixes, chacun sur un nombre d'octets défini. `struct.unpack` traduit une tranche d'octets en valeurs Python selon un **format** :

```python
import struct

# Ex. un en-tête : magic (2 octets), version (u16), nb_records (u32), le tout little-endian
magic, version, nb = struct.unpack("<2sHI", donnees[:8])
#                                    │ │ │└ I : uint32 (4 octets)
#                                    │ │ └─ H : uint16 (2 octets)
#                                    │ └─── 2s : 2 octets bruts (bytes)
#                                    └───── < : little-endian (ordre des octets)
```

Les codes de format essentiels :

| Code | Type | Octets |
|---|---|---|
| `B` / `b` | uint8 / int8 | 1 |
| `H` / `h` | uint16 / int16 | 2 |
| `I` / `i` | uint32 / int32 | 4 |
| `f` / `d` | float32 / float64 | 4 / 8 |
| `Ns` | N octets bruts | N |

L'**endianness** (`<` little / `>` big) est l'ordre des octets d'un nombre multi-octets : `0x002A` peut se stocker `2A 00` (little, le plus répandu, x86/ARM) ou `00 2A` (big, réseau). Se tromper de sens donne des nombres absurdes — c'est le premier réflexe de debug. `struct.calcsize("<2sHI")` donne la taille (8) : indispensable pour avancer d'un champ à l'autre par offsets.

## 3. Le format FIT, de haut niveau

FIT (Flexible and Interoperable Data Transfer, standard Garmin/ANT) est plus riche qu'un simple en-tête : il est **auto-descriptif**. Sa structure :

- un **header** (taille, version du protocole, taille des données, tag `.FIT`) ;
- une suite de **messages**, chacun précédé d'un octet d'en-tête indiquant son type ;
- des messages de **définition** (« voici les champs du prochain type de record : timestamp sur 4 octets, FC sur 1 octet... ») suivis des messages de **données** qui les remplissent ;
- un **CRC** final de contrôle d'intégrité.

Écrire un décodeur FIT complet à la main serait des centaines de lignes (et le SDK évolue). On délègue à `fitparse` — mais comprendre `struct` (§2) est ce qui rend ce format non magique : `fitparse` fait, en gros, du `struct.unpack` piloté par les messages de définition.

## 4. fitparse : lire une séance

```bash
pip install fitparse
```

```python
from fitparse import FitFile

fit = FitFile("seance.fit")

# Quels types de messages contient le fichier ?
types = {msg.name for msg in fit.get_messages()}
# {'file_id', 'record', 'lap', 'session', 'event', 'device_info', ...}

# Les 'record' : un point de mesure par seconde
for record in fit.get_messages("record"):
    valeurs = {champ.name: champ.value for champ in record}
    # {'timestamp': datetime(...), 'heart_rate': 148, 'power': 210,
    #  'speed': 4.35, 'altitude': 112.4, 'position_lat': 578..., ...}
    break
```

Les messages qui comptent pour toi : **`record`** (la série temporelle seconde par seconde), **`lap`** (les tours/intervalles), **`session`** (le résumé global : distance, durée, FC moyenne). Chaque champ a un `.name`, une `.value` et parfois une `.units`.

## 5. Les pièges d'unités

FIT stocke des entiers pour la compacité — les vraies unités demandent conversion (généralement gérée par fitparse, mais à connaître) :

| Donnée | Stockage FIT | Conversion |
|---|---|---|
| Position (lat/lon) | **semicircles** (int32) | `degrés = semicircles × (180 / 2³¹)` |
| Vitesse | mm/s ou m/s | m/s → km/h : `× 3.6` ; → allure min/km : `1000 / (m/s × 60)` |
| Distance | centimètres | `/ 100` pour des mètres |
| Altitude | (alt + 500) × 5 | souvent déjà converti par fitparse |
| Timestamp | secondes depuis 1989-12-31 | fitparse renvoie un `datetime` |

Règle : vérifie toujours `.units` et un ordre de grandeur (une vitesse de 4350 « quelque chose » est des mm/s, pas des km/h). La position en semicircles est le piège classique — un lat de `578000000` est normal (× 8.38e-8 ≈ 48.4°).

## 6. Des records au DataFrame

Le pont vers les chapitres 10-11 : transformer le flux de records en `DataFrame` indexé par le temps.

```python
import pandas as pd

def fit_vers_dataframe(chemin: str) -> pd.DataFrame:
    fit = FitFile(chemin)
    lignes = [{champ.name: champ.value for champ in rec}
              for rec in fit.get_messages("record")]
    df = pd.DataFrame(lignes)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.set_index("timestamp").sort_index()
```

Réalités du terrain à gérer (chapitre 10 appliqué) :

- **Champs manquants** : pas de capteur de puissance → colonne `power` absente ou pleine de NaN. Ne jamais présumer qu'une colonne existe (`df.get("power")`, ou vérifier `"power" in df.columns`).
- **Trous de timestamps** : pauses, perte de signal GPS → l'index n'est pas régulier. `df.asfreq("s")` pour matérialiser, ou détecter les pauses par `df.index.to_series().diff() > seuil`.
- **Valeurs aberrantes** : FC à 0 (capteur décroché), altitude délirante (GPS) → nettoyage du chapitre 10.

Une fois le DataFrame propre, tout le chapitre 11 s'applique : zones de FC (`pd.cut`), moyennes glissantes de puissance, temps par zone — et le chapitre 12 pour le profil de séance (FC/puissance en subplots).

## 7. Robustesse : fichiers réels

Les fichiers `.fit` du monde réel sont parfois tronqués (batterie morte en pleine séance), corrompus, ou d'un fabricant exotique. Le décodage doit dégrader proprement :

```python
from fitparse import FitFile
from fitparse.utils import FitParseError

def charger_fit(chemin: str) -> pd.DataFrame:
    try:
        fit = FitFile(chemin)
        fit.parse()
    except FitParseError as exc:
        raise SeanceIllisible(f"{chemin} : fichier FIT invalide ({exc})") from exc
    ...
```

Comme pour le JSON (chapitre 5) et les API (chapitre 9) : traduire l'erreur technique en exception métier, ne jamais laisser un fichier pourri crasher un import de lot (chapitre 4 : logger et continuer).

## Checklist de fin de chapitre

- [ ] Je distingue `bytes` et `str`, je lis en `"rb"` et j'inspecte avec `.hex()`.
- [ ] Je décode des champs binaires avec `struct.unpack` (formats, endianness, offsets).
- [ ] Je comprends la structure FIT (header, définitions, records, laps, session).
- [ ] J'extrais records/laps/session avec `fitparse` en gérant les champs absents.
- [ ] Je connais les pièges d'unités (semicircles, vitesse, distance) et je vérifie `.units`.
- [ ] Je transforme un `.fit` en DataFrame propre, trous et capteurs manquants gérés, avec exception métier sur fichier invalide.
