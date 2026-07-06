Les métriques du chapitre 11 sont justes mais illisibles en tableau. Ce chapitre les rend visibles : **Matplotlib** pour comprendre vite (et produire des PNG), **Plotly** pour explorer (zoom, survol, HTML interactif). Les deux se branchent directement sur tes DataFrames.

```bash
pip install matplotlib plotly
```

## 1. Matplotlib : Figure et Axes

L'API qui évite 90 % des confusions est l'API **orientée objet** : une `Figure` (la toile) contient des `Axes` (les graphiques). Toujours démarrer par `plt.subplots` :

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(cours.index, cours["IWDA"], label="IWDA", linewidth=1.2)
ax.plot(cours.index, cours["mm50"], label="MM 50 j", linestyle="--")

ax.set_title("IWDA — cours et moyenne mobile")
ax.set_xlabel("")                       # les dates se comprennent seules
ax.set_ylabel("Cours (€)")
ax.legend()
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig("iwda.png", dpi=150)        # export PNG
plt.show()                              # ou affichage interactif
```

Évite le style `plt.plot(...)` global (état implicite « le graphique courant ») : avec `fig, ax` explicites, plusieurs graphiques coexistent sans surprise.

Les annotations qui font la différence :

```python
ax.axhline(100, color="grey", linestyle=":")            # ligne de référence
ax.axvspan(pic, creux, alpha=0.15, color="red")         # période surlignée (drawdown !)
ax.annotate("creux", xy=(creux, v_creux),
            xytext=(creux, v_creux * 1.1),
            arrowprops={"arrowstyle": "->"})
```

## 2. Multi-graphiques : subplots

Pour une séance (FC en haut, puissance en bas) ou un cours + son drawdown, les axes **partagent l'axe X** :

```python
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                               height_ratios=[2, 1])
ax1.plot(cours.index, cours["valeur"])
ax2.fill_between(dd.index, dd, 0, color="red", alpha=0.4)   # aire de drawdown
ax2.set_ylabel("Drawdown")
```

`sharex=True` : zoomer/aligner l'un aligne l'autre — indispensable dès que deux courbes racontent la même chronologie. `fill_between` remplit une aire (drawdowns, zones cardiaques, bandes de volatilité).

Pandas offre un raccourci honnête : `df.plot(ax=ax)` trace chaque colonne — pratique pour l'exploration, mais garde la main sur `ax` pour les titres/légendes.

## 3. Choisir le bon graphique

| Question | Graphique |
|---|---|
| Évolution dans le temps | courbe (`plot`) |
| Comparaison d'évolutions | courbes en **base 100** |
| Comparaison de catégories | barres (`bar`/`barh`) |
| Répartition d'un total | barres empilées ou camembert (avec parcimonie) |
| Distribution d'une variable | histogramme (`hist`) |
| Relation entre deux variables | nuage (`scatter`) |

Deux règles d'honnêteté : comparer des évolutions exige la **même base** (base 100 — chapitre 11) ; et l'axe Y des barres démarre à 0 (tronquer l'axe amplifie visuellement des écarts minuscules).

## 4. Plotly Express : l'interactif en une ligne

Plotly produit du HTML interactif : survol → valeurs exactes, zoom à la souris, légende cliquable (masquer une série). `plotly.express` en est l'API haut niveau, pensée pour les DataFrames :

```python
import plotly.express as px

fig = px.line(base100.reset_index(), x="date", y=["IWDA", "EMIM"],
              title="Comparaison base 100")
fig.update_layout(yaxis_title="Base 100", legend_title="")

fig.show()                                   # ouvre dans le navigateur
fig.write_html("comparaison.html",           # fichier autonome, partageable
               include_plotlyjs="cdn")       # léger (JS chargé depuis le CDN)
```

Les équivalents : `px.line`, `px.bar`, `px.scatter`, `px.histogram`, `px.pie`. Le paramètre `hover_data=` enrichit l'info-bulle (ex. la valeur exacte ET le rendement du jour). Plotly Express attend des données « longues » (une colonne par variable) : `reset_index()` et parfois `df.melt(...)` sont tes amis.

Sous Express vit `plotly.graph_objects` (`go.Figure`, `go.Scatter`) pour le contrôle fin — tu y recourras rarement, mais `fig.add_hline`, `fig.add_vrect` (l'équivalent d'axvspan) s'utilisent directement sur une figure Express :

```python
fig.add_vrect(x0=pic, x1=creux, fillcolor="red", opacity=0.15, line_width=0)
```

## 5. Matplotlib ou Plotly ?

| Critère | Matplotlib | Plotly |
|---|---|---|
| Sortie | PNG/PDF statique | HTML interactif |
| Usage type | rapport figé, README, publication | exploration, dashboard, partage |
| Contrôle typographique fin | excellent | correct |
| Zoom/survol | non | natif |
| Dans Streamlit (ch. 13) | `st.pyplot` | `st.plotly_chart` (le plus intégré) |

Réflexe simple : **comprendre → Matplotlib, montrer → Plotly**. Les deux consomment les mêmes DataFrames — bien séparer calcul (chapitre 11) et rendu permet de changer d'avis sans retoucher les données.

## 6. Lisibilité : la checklist de chaque graphique

Un graphique sans titre ni unités est un brouillon. Avant de livrer :

- **Titre** qui énonce le message (« IWDA : -18 % de drawdown en 2025 »), pas juste le contenu (« Cours IWDA »).
- **Axes étiquetés avec unités** (€, %, h/semaine) ; format pourcentage pour les rendements (`ax.yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))`).
- **Légende** dès la deuxième série ; couleurs cohérentes d'un graphique à l'autre (IWDA toujours de la même couleur).
- Grille discrète (`alpha=0.3`), pas de décor inutile.
- Sources/période mentionnées si le graphique voyage seul.

## Checklist de fin de chapitre

- [ ] Je démarre tout graphique par `fig, ax = plt.subplots()` et je sais titrer/légender/exporter.
- [ ] Je construis des subplots à axe X partagé et j'annote (axvspan, axhline, fill_between).
- [ ] Je choisis le type de graphique selon la question, et je compare en base 100.
- [ ] Je produis un HTML interactif Plotly (`px.line`, hover, `write_html`).
- [ ] Je sais quand préférer Matplotlib (figé) et Plotly (interactif).
- [ ] Chaque graphique livré passe la checklist de lisibilité.
