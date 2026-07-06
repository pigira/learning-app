Tes analyses des chapitres 2 et 6 (boucles d'accumulation, GROUP BY) trouvent ici leur outil définitif : Pandas. Un `DataFrame` = un tableau typé, indexé, avec des opérations vectorisées — pense « SQL + Excel + NumPy » avec une API Python. C'est l'outil central des projets Finance et Enduro.

```bash
pip install pandas
```

## 1. Series et DataFrame

- **Series** : une colonne (valeurs + index + dtype).
- **DataFrame** : un tableau de colonnes alignées sur un index commun.

```python
import pandas as pd

df = pd.read_csv("data/seances.csv")     # la porte d'entrée n°1

df.head()          # 5 premières lignes — TOUJOURS regarder d'abord
df.info()          # colonnes, dtypes, non-null count — LE diagnostic
df.describe()      # stats descriptives des colonnes numériques
df.shape           # (n_lignes, n_colonnes)
df["sport"].value_counts()    # comptage des valeurs d'une colonne
```

Le réflexe d'inspection `head / info / describe` ouvre **toute** session Pandas : les dtypes racontent l'état des données (`duree_min` en `object` = il y a du texte caché dedans).

`read_csv` sait presque tout faire dès le chargement :

```python
df = pd.read_csv("data/seances.csv", parse_dates=["date"],
                 dtype={"fc_moy": "Int64"})     # Int64 (nullable) : int AVEC NaN possibles
```

## 2. Sélectionner

```python
df["duree_min"]                  # une colonne → Series
df[["date", "sport"]]            # plusieurs → DataFrame

df.loc[3]                        # ligne par ÉTIQUETTE d'index
df.iloc[0]                       # ligne par POSITION
df.loc[2:5, ["date", "sport"]]   # lignes ET colonnes (loc : bornes INCLUSES)
```

Le **filtre booléen** est l'outil quotidien :

```python
df[df["duree_min"] > 45]                          # comme la comprehension du ch. 2
df[(df["sport"] == "course") & (df["fc_moy"] > 150)]   # & | ~ — PAS and/or,
                                                        # et parenthèses OBLIGATOIRES
df[df["sport"].isin(["course", "velo"])]
df.query("sport == 'course' and duree_min > 45")  # variante lisible
```

## 3. Colonnes dérivées : penser vectorisé

Les opérations s'appliquent à des colonnes **entières** — pas de boucle :

```python
df["duree_h"] = df["duree_min"] / 60
df["allure"] = df["duree_min"] / df["distance_km"]        # ligne à ligne, aligné
df["longue"] = df["duree_min"] > 60                        # colonne booléenne
df["sport"] = df["sport"].str.lower().str.strip()          # méthodes str vectorisées
```

La règle : si tu écris `for i in range(len(df))`, tu combats l'outil — cherche l'opération vectorisée (100 à 1000× plus rapide, et plus lisible). `apply(fonction)` existe pour les cas irréductibles, en dernier recours :

```python
df["zone"] = df["fc_moy"].apply(lambda fc: zone_cardiaque(fc, 185))   # acceptable
# mieux, vectorisé : pd.cut(df["fc_moy"], bins=[0, 111, 129, 148, 166, 999],
#                            labels=[1, 2, 3, 4, 5])
```

## 4. groupby : l'agrégation

Le `GROUP BY` de SQL (chapitre 6) et l'idiome d'accumulation (chapitre 2), en une ligne :

```python
df.groupby("sport")["duree_min"].sum()          # total par sport
df.groupby("sport").agg(                        # agrégations NOMMÉES — le style à adopter
    total_min=("duree_min", "sum"),
    nb_seances=("date", "count"),
    fc_moyenne=("fc_moy", "mean"),
    plus_longue=("duree_min", "max"),
)
df.groupby(["sport", "longue"]).size()          # multi-clés
```

Mécanique **split-apply-combine** : découper en groupes, appliquer l'agrégat à chacun, recombiner. Le résultat est indexé par les clés de groupe (`reset_index()` pour revenir à des colonnes plates).

## 5. merge et concat : croiser

```python
# merge = JOIN SQL
valo = positions.merge(cours, on="ticker", how="left")
#   how="inner" : intersection ; "left" : garde toutes les positions,
#   cours manquant → NaN (l'équivalent exact du LEFT JOIN du chapitre 6)

# concat = empiler des morceaux de même structure (des CSV mensuels, par ex.)
annee = pd.concat([janvier, fevrier, mars], ignore_index=True)
```

Vérifie toujours la taille après un merge : des clés dupliquées à droite **multiplient** les lignes (produit cartésien partiel) — le bug de merge classique se détecte par un simple `len(avant) == len(après)`.

## 6. Nettoyage : le vrai travail

Les données réelles arrivent sales. L'arsenal :

```python
# Diagnostic
df.isna().sum()                    # NaN par colonne
df.duplicated().sum()              # doublons stricts
df["sport"].unique()               # valeurs réelles ("course", "Course ", "COURSE"...)

# Types
df["date"] = pd.to_datetime(df["date"], format="mixed")   # str → datetime
df["duree_min"] = pd.to_numeric(df["duree_min"], errors="coerce")
#                       errors="coerce" : l'imparsable devient NaN (à traiter ensuite)

# Valeurs manquantes — PAR COLONNE, jamais en aveugle
df = df.dropna(subset=["date", "duree_min"])     # sans date/durée : inexploitable
df["fc_moy"] = df["fc_moy"].fillna(df["fc_moy"].median())   # FC : imputable
df["distance_km"] = df["distance_km"].fillna(0.0)           # renfo : 0 est correct

# Normalisation et doublons
df["sport"] = df["sport"].str.lower().str.strip()
df = df.drop_duplicates(subset=["date", "sport"], keep="first")
```

Chaque `fillna`/`dropna` est une **décision métier**, pas un geste technique : supprimer une séance sans durée est défendable, mettre 0 à une FC manquante fausserait toutes les moyennes (NaN est correctement ignoré par `mean()` — comme AVG en SQL). Documente ces choix en commentaire.

## 7. Entrées/sorties

```python
df.to_csv("export.csv", index=False)             # index=False sinon colonne parasite

import sqlite3
conn = sqlite3.connect("data/enduro.db")
df = pd.read_sql("SELECT * FROM seances WHERE sport = ?", conn, params=("course",))
df.to_sql("seances_propres", conn, if_exists="replace", index=False)
```

`read_sql` relie ce chapitre au chapitre 6 : SQL pour stocker et pré-filtrer, Pandas pour analyser. Excel : `pip install openpyxl` puis `read_excel`/`to_excel` — même logique.

## 8. SQL ou Pandas ?

| Situation | Outil |
|---|---|
| Stockage durable, accès concurrent, filtres simples | SQLite |
| Nettoyage, colonnes dérivées, stats, données « larges » | Pandas |
| Agrégat simple sur grosse table | SQL (ne charge pas 1M de lignes pour un SUM) |
| Analyse exploratoire, croisements multiples | Pandas |

Le pattern de tes projets : SQLite comme source de vérité → `read_sql` un sous-ensemble → Pandas pour l'analyse → résultats vers l'affichage (chapitres 12-13).

## Checklist de fin de chapitre

- [ ] Réflexe `head / info / describe` avant toute manipulation ; je lis les dtypes comme un diagnostic.
- [ ] Je sélectionne avec loc/iloc et les filtres booléens (`&`, `|`, parenthèses).
- [ ] Je crée des colonnes dérivées vectorisées — zéro boucle sur les lignes.
- [ ] `groupby` + agrégations nommées, `merge` avec `how=` choisi et taille vérifiée.
- [ ] Je nettoie colonne par colonne (to_datetime, to_numeric coerce, fillna/dropna justifiés, drop_duplicates).
- [ ] Je fais circuler les données entre SQLite et Pandas (`read_sql`, `to_sql`) et je sais lequel utiliser quand.
