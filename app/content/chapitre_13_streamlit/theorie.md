Le rapport HTML du chapitre 12 est figé : pas de filtre, pas d'upload, pas de saisie. Streamlit transforme tes scripts Pandas/Plotly en **applications web interactives** — sans HTML, sans JS, sans routes. C'est l'interface des trois projets (dashboard Finance, suivi Enduro, carnet Cuisine), et l'outil de prototypage le plus rentable de ta boîte à outils.

```bash
pip install streamlit
streamlit run app.py          # ouvre http://localhost:8501
```

## 1. Le modèle mental : tout re-tourne, à chaque interaction

Un fichier Streamlit est un **script ordinaire, ré-exécuté en entier** à chaque interaction (clic, saisie, sélection). Pas de callbacks, pas d'état caché : le script se relit de haut en bas et redessine tout.

```python
import streamlit as st

st.title("Suivi Enduro")
sport = st.selectbox("Sport", ["course", "velo", "natation"])   # widget
st.write(f"Sport sélectionné : {sport}")
```

Quand tu changes le selectbox : le script ENTIER re-tourne, `st.selectbox` renvoie la nouvelle valeur, la page se redessine. Ce modèle rend le code trivial à lire — et il a deux conséquences directes : le travail coûteux doit être **caché** (§4) et l'état qui doit survivre au re-run doit être **stocké** (§5). Tout Streamlit tient dans ces deux conséquences.

## 2. Widgets : les entrées

```python
ticker = st.selectbox("ETF", ["IWDA", "EMIM", "WSML"])
periode = st.slider("Période (mois)", 1, 36, value=12)
debut, fin = st.date_input("Plage", value=(date(2026, 1, 1), date(2026, 6, 30)))
seuil = st.number_input("Durée min (min)", value=30)
ok = st.checkbox("Inclure la natation", value=True)
sports = st.multiselect("Sports", options=liste, default=liste)
fichier = st.file_uploader("Export CSV", type="csv")     # → objet lisible par read_csv
if st.button("Recalculer"):
    ...                                # True UNIQUEMENT le run du clic
```

Chaque widget **renvoie sa valeur courante** — le code en aval l'utilise comme n'importe quelle variable. Un `st.button` vaut `True` seulement pendant le run déclenché par le clic (piège classique : ne t'en sers pas pour « activer » durablement quelque chose — c'est le rôle de session_state ou d'une checkbox).

## 3. Affichage : sorties et layout

```python
st.metric("Volume ce mois", "14.5 h", delta="+2.3 h")     # le chiffre-clé
st.dataframe(df)                        # tableau interactif (tri, recherche)
st.plotly_chart(fig, use_container_width=True)            # tes figures du ch. 12
st.pyplot(fig_matplotlib)
st.markdown("**Markdown** complet, `code`, tableaux...")
```

Structure de page :

```python
st.sidebar.header("Filtres")                    # barre latérale : les contrôles
sport = st.sidebar.selectbox(...)

col1, col2, col3 = st.columns(3)                # métriques côte à côte
col1.metric("Séances", nb)
col2.metric("Heures", f"{h:.1f}")

onglet1, onglet2 = st.tabs(["Synthèse", "Détail"])
with onglet1:
    st.plotly_chart(...)

with st.expander("Données brutes"):
    st.dataframe(df)
```

Convention efficace : **filtres dans la sidebar, résultats dans la page** — metrics en haut (columns), graphiques ensuite, tableau en expander.

## 4. `@st.cache_data` : ne pas recalculer le monde

Re-exécution totale + chargement de données = catastrophe (le CSV relu, l'API rappelée à chaque clic). Le cache mémoïse par arguments :

```python
@st.cache_data
def charger_seances(chemin: str) -> pd.DataFrame:
    return nettoyer(pd.read_csv(chemin))        # exécuté UNE fois par `chemin`

@st.cache_data(ttl=900)                          # expire après 15 min
def cours_api(ticker: str) -> pd.DataFrame:
    return client.historique(ticker)             # API rappelée au plus tous les 1/4 h
```

Mêmes arguments → résultat servi depuis le cache (copie défensive incluse : muter le retour est sans danger). Règles : cacher les fonctions **pures et coûteuses** (I/O, API, gros calculs) ; `ttl=` pour les données qui périment ; jamais de widget dans une fonction cachée. (`st.cache_resource` existe pour les objets non-copiables : connexion DB, modèle ML.)

## 5. `st.session_state` : l'état qui survit

Les variables ordinaires meurent à chaque re-run. Pour un panier, un formulaire cumulatif, un historique de conversation :

```python
if "recettes" not in st.session_state:          # init au premier run seulement
    st.session_state.recettes = []

with st.form("ajout"):                           # form : soumission atomique
    nom = st.text_input("Nom")
    temps = st.number_input("Temps (min)", min_value=1, value=20)
    if st.form_submit_button("Ajouter"):
        st.session_state.recettes.append({"nom": nom, "temps": temps})

for i, r in enumerate(st.session_state.recettes):
    col1, col2 = st.columns([4, 1])
    col1.write(f"{r['nom']} — {r['temps']} min")
    if col2.button("Suppr.", key=f"suppr_{i}"):  # key UNIQUE par widget répété
        st.session_state.recettes.pop(i)
        st.rerun()                                # redessine immédiatement
```

Trois points : l'init idiomatique `if ... not in st.session_state` ; `st.form` regroupe des saisies et ne re-exécute qu'à la soumission (sinon chaque frappe re-run) ; les widgets créés en boucle exigent un `key=` unique. Les widgets eux-mêmes vivent dans session_state via leur key — un `st.selectbox(..., key="sport")` se relit avec `st.session_state.sport`.

## 6. Structurer une vraie app

Le fichier app.py ne contient QUE la présentation ; les calculs restent dans tes modules :

```
enduro_app/
├── app.py                # page principale (ou accueil)
├── pages/                # multi-pages AUTOMATIQUE (préfixe = ordre)
│   ├── 1_Seances.py
│   └── 2_Charge.py
└── pipeline/             # le package du chapitre 10 — INCHANGÉ
```

Le dossier `pages/` crée la navigation tout seul. La règle d'or vient des chapitres 4 et 7 : `app.py` importe `pipeline.coeur` et l'affiche — si une logique n'est testable qu'en lançant Streamlit, elle est au mauvais endroit. Symptôme à surveiller : un `if st.checkbox(...)` au milieu d'un calcul.

Anti-patterns résumés : logique métier dans app.py ; oubli du cache (app qui rame) ; état dans des variables globales (perdu ou partagé entre utilisateurs) ; `st.button` utilisé comme interrupteur durable.

## Checklist de fin de chapitre

- [ ] Je peux expliquer le cycle re-run et ses deux conséquences (cache, session_state).
- [ ] Je construis une page filtres-sidebar / metrics / graphiques / tableau.
- [ ] Je cache les chargements avec `@st.cache_data` (et `ttl` pour les données périssables).
- [ ] Je gère un état cumulatif avec `session_state` + `st.form` + `key=` uniques.
- [ ] Mon app importe mes modules métier — elle ne contient que de l'affichage.
- [ ] Je sais créer une app multi-pages avec le dossier `pages/`.
