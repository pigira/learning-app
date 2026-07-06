Cours d'ETF, charge d'entraînement : tes données ont un axe temps, et les questions intéressantes sont temporelles — rendement mensuel, moyenne mobile, pire chute, charge de la semaine. Pandas a un outillage dédié : `DatetimeIndex`, `resample`, `rolling`, et une poignée de méthodes (`pct_change`, `shift`, `cummax`) qui suffisent à calculer toutes les métriques finance/sport de tes projets.

## 1. DatetimeIndex : le temps comme index

Tout part d'un index de dates trié :

```python
import pandas as pd

df = pd.read_csv("cours.csv", parse_dates=["date"])
df = df.set_index("date").sort_index()      # trié : indispensable pour la suite
```

Ce que l'index temporel débloque :

```python
df.loc["2026-03"]                    # tout mars (sélection partielle)
df.loc["2026-01":"2026-06"]          # janvier à juin INCLUS
df.loc["2026-06-15":]                # depuis mi-juin
df.index.dayofweek                   # composantes : .month, .year, .isocalendar()
df.asfreq("D")                       # matérialise les jours manquants (NaN)
```

Deux pièges : un index non trié rend le slicing incohérent (toujours `sort_index()`), et les week-ends/jours fériés font que les cours boursiers n'ont PAS une fréquence régulière — les trous sont normaux, les méthodes qui suivent les gèrent.

## 2. resample : changer de granularité

`resample` = un `groupby` par période. Quotidien → mensuel, séances éparses → semaines complètes :

```python
mensuel = cours.resample("ME").last()      # dernier cours de chaque mois
hebdo_h = seances["duree_h"].resample("W").sum()   # heures par semaine

cours_quotidien = cours.resample("D").ffill()      # combler les trous :
                                                    # week-end = dernier cours connu
```

Fréquences usuelles : `D` (jour), `W` (semaine), `ME` (fin de mois), `QE` (trimestre), `YE` (année). L'agrégation se choisit selon la nature de la donnée : un **cours** se rééchantillonne en `last()` (ou `ohlc()`), un **volume** d'entraînement en `sum()`, une FC en `mean()`.

Important pour le sport : `resample("D").sum()` sur des séances éparses produit des **zéros explicites** les jours de repos — exactement ce qu'il faut pour les moyennes glissantes de charge (un jour sans sport compte pour 0, il ne disparaît pas).

## 3. rolling : fenêtres glissantes

```python
cours["mm20"] = cours["valeur"].rolling(20).mean()          # moyenne mobile 20 j
cours["mm20"] = cours["valeur"].rolling(20, min_periods=1).mean()   # démarre dès j1

charge_7j = charge_quotidienne.rolling(7).sum()             # charge aiguë
charge_28j = charge_quotidienne.rolling(28).sum() / 4       # chronique (hebdo moyen)
```

- Les `n-1` premières valeurs sont NaN (fenêtre incomplète) sauf si `min_periods` l'autorise — choix à faire en conscience : une « moyenne 20 jours » sur 3 points ment un peu.
- `rolling` respecte l'ordre de l'index, d'où l'importance du tri initial.
- Variantes : `.std()` (volatilité glissante), `.max()`, `.apply(...)`.

Le ratio **charge aiguë / charge chronique** (ACWR, 7 j vs 28 j) est LA métrique de suivi d'entraînement : au-dessus de ~1.5, le risque de blessure grimpe — c'est un exercice de ce chapitre.

## 4. Rendements : pct_change, cumprod, shift

```python
rdt = cours["valeur"].pct_change()          # (v_t - v_{t-1}) / v_{t-1} — rendement simple
rdt_mensuel = cours["valeur"].resample("ME").last().pct_change()

perf_cumulee = (1 + rdt).cumprod() - 1      # performance composée depuis le début
base100 = 100 * cours["valeur"] / cours["valeur"].iloc[0]   # comparaison visuelle
```

La **composition** est la propriété centrale : les rendements s'enchaînent en produit, pas en somme — `(1+r1)(1+r2)... - 1`, et c'est ce que `cumprod` calcule. Vérification classique : la composition des rendements mensuels doit redonner exactement la performance totale.

`shift(n)` décale une série de n pas — c'est l'outil anti-**lookahead** (utiliser une info du futur) :

```python
df["rdt_veille"] = df["rdt"].shift(1)       # au jour t, le rendement de t-1
```

Toute règle du type « si le rendement d'hier était positif... » s'écrit avec `shift(1)` : au moment de décider en t, seul t-1 est connu. L'oubli du shift est LE bug des backtests amateurs.

## 5. Volatilité et drawdown

**Volatilité** = écart-type des rendements, annualisé en √252 (jours de bourse par an) :

```python
vol_annuelle = rdt.std() * (252 ** 0.5)          # ex. 0.18 → 18 % par an
vol_glissante = rdt.rolling(60).std() * (252 ** 0.5)
```

**Drawdown** = la baisse depuis le plus haut atteint — la métrique qui fait mal :

```python
plus_haut = cours["valeur"].cummax()             # plus haut historique courant
drawdown = cours["valeur"] / plus_haut - 1       # ≤ 0, en %
max_dd = drawdown.min()                          # ex. -0.34 : -34 %

creux = drawdown.idxmin()                        # date du pire point
pic = cours.loc[:creux, "valeur"].idxmax()       # le sommet d'avant
```

`cummax` (maximum cumulé) fait tout le travail : à chaque date, le plus haut vu jusque-là. La date de récupération est la première date après le creux où le cours re-dépasse le pic.

## 6. Rendement annualisé et comparaison de périodes

```python
n_annees = (cours.index[-1] - cours.index[0]).days / 365.25
perf_totale = cours["valeur"].iloc[-1] / cours["valeur"].iloc[0] - 1
rdt_annualise = (1 + perf_totale) ** (1 / n_annees) - 1     # moyenne GÉOMÉTRIQUE

par_annee = cours["valeur"].resample("YE").last().pct_change()   # rendements civils
```

L'annualisation est géométrique (racine n-ième de la performance composée), jamais `perf_totale / n_annees` — la moyenne arithmétique surestime systématiquement.

Pour comparer deux ETF : les ramener en **base 100** sur leur **période commune** (`df.dropna()` après un join des deux séries) — comparer des périodes différentes n'a aucun sens.

## 7. Le tableau de bord des métriques

| Métrique | Formule Pandas |
|---|---|
| Rendements journaliers | `v.pct_change()` |
| Performance totale | `v.iloc[-1] / v.iloc[0] - 1` |
| Performance annualisée | `(1 + perf) ** (1 / n_annees) - 1` |
| Volatilité annualisée | `rdt.std() * sqrt(252)` |
| Moyenne mobile n | `v.rolling(n).mean()` |
| Max drawdown | `(v / v.cummax() - 1).min()` |
| Rendements mensuels / annuels | `v.resample("ME"/"YE").last().pct_change()` |
| Charge aiguë / chronique | `q.rolling(7).sum()` / `q.rolling(28).sum() / 4` |

Huit lignes de Pandas = tout le rapport de performance du projet Finance et le suivi de charge du projet Enduro. La difficulté n'est pas le code, c'est de savoir **ce que chaque nombre veut dire** — les exercices s'en chargent.

## Checklist de fin de chapitre

- [ ] Je mets les dates en index trié et je slice par période (`loc["2026-03"]`).
- [ ] Je choisis la bonne agrégation de `resample` selon la nature de la donnée (last/sum/mean).
- [ ] Je manie `rolling` (NaN de démarrage, min_periods) pour moyennes mobiles et charges.
- [ ] Rendements : pct_change, composition par cumprod, annualisation géométrique.
- [ ] Je calcule volatilité annualisée et max drawdown (avec dates de pic/creux).
- [ ] `shift(1)` systématique dès qu'une décision en t utilise une info de t-1 — jamais de lookahead.
