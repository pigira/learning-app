Jusqu'ici tu vérifiais ton code en le lançant et en regardant la sortie. Ça ne passe pas à l'échelle : chaque modification risque de casser silencieusement ce qui marchait. Les tests automatisés sont le filet qui rend le refactoring possible — et `pytest` rend leur écriture presque agréable. En bonus : l'outillage qualité (`ruff`, `black`, `coverage`) qui automatise ce que tu faisais à la main depuis le chapitre 0.

## 1. pytest : la base

```bash
pip install pytest
```

Un test = une fonction `test_*` dans un fichier `test_*.py`, avec des `assert` nus :

```python
# tests/test_calculs.py
from entrainement.calculs import allure_min_km, zone_cardiaque


def test_allure_10km_52min():
    assert allure_min_km(10.0, 52) == (5, 12)


def test_zone_seuil_haut():
    assert zone_cardiaque(178, 185) == 5
```

```bash
python -m pytest            # découvre et lance tout tests/test_*.py
python -m pytest -v         # une ligne par test
python -m pytest -k zone    # filtre par nom
python -m pytest -x         # stop au premier échec
```

En cas d'échec, pytest **réécrit l'assert** pour montrer les valeurs réelles :

```
E       assert (5, 13) == (5, 12)
```

C'est toute la différence avec un `assert` C : pas besoin de message, l'introspection fait le travail.

Structure conventionnelle : un dossier `tests/` à la racine, miroir des modules (`tests/test_calculs.py` pour `entrainement/calculs.py`). Les tests s'organisent en **arrange / act / assert** : préparer les données, appeler LA fonction testée, vérifier.

## 2. Tester les cas qui comptent

Un bon test ne re-teste pas le cas nominal dix fois, il couvre les **frontières** :

```python
import pytest


def test_zone_borne_exacte_60_pourcent():
    assert zone_cardiaque(111, 185) == 2        # 60.0 % pile : borne incluse


def test_fc_aberrante_leve():
    with pytest.raises(FcInvalide):             # le test PASSE si l'exception part
        zone_cardiaque(320, 185)


def test_message_derreur_utile():
    with pytest.raises(FcInvalide, match="320"):   # le message cite la valeur
        zone_cardiaque(320, 185)
```

`pytest.raises` transforme « ça doit planter » en assertion : les chemins d'erreur du chapitre 4 se testent aussi.

## 3. `parametrize` : une table de cas, un seul test

Les tests de frontières explosent vite en copier-coller. La table de cas les factorise :

```python
@pytest.mark.parametrize(
    ("fc", "fc_max", "zone_attendue"),
    [
        (100, 185, 1),
        (111, 185, 2),      # 60 % pile
        (129, 185, 2),
        (130, 185, 3),      # 70 % (arrondi) : bascule
        (148, 185, 4),
        (167, 185, 5),      # 90 % pile
        (185, 185, 5),
    ],
)
def test_zones(fc, fc_max, zone_attendue):
    assert zone_cardiaque(fc, fc_max) == zone_attendue
```

pytest génère **un test par ligne** (7 ici), chacun nommé et rapporté séparément. Ajouter un cas limite = ajouter une ligne. C'est l'outil n°1 pour tester du code de calcul (zones, allures, rendements, parsing).

## 4. Fixtures : préparer et nettoyer

Une **fixture** fournit à un test ce dont il a besoin (données, connexion, fichier), avec nettoyage automatique. Injection par nom de paramètre :

```python
import sqlite3
import pytest


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")          # une base NEUVE par test
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO recettes (nom, temps_min) VALUES (?, ?)",
                     [("omelette", 10), ("risotto", 45)])
    yield conn                                  # ← le test s'exécute ici
    conn.close()                                # nettoyage, même si le test échoue


def test_plus_rapide(db):                       # pytest voit le paramètre "db"
    nom = plus_rapide(db)
    assert nom == "omelette"
```

Même mécanique que `@contextmanager` (chapitre 5) : avant le `yield` = setup, après = teardown. Chaque test reçoit sa propre base : **isolation** — l'ordre des tests ne compte jamais.

Fixtures intégrées à connaître :

- `tmp_path` : un dossier temporaire unique, nettoyé après le test — parfait pour tester la persistance JSON/CSV du chapitre 5 sans polluer le disque.
- `capsys` : capture stdout/stderr (`capsys.readouterr().out`) pour tester les affichages.
- `monkeypatch` : remplace temporairement n'importe quoi — LA solution pour tester du code interactif :

```python
def test_saisie_redemande(monkeypatch, capsys):
    reponses = iter(["abc", "99", "8"])                    # scénario de frappe
    monkeypatch.setattr("builtins.input", lambda _: next(reponses))
    assert saisie_entier("Portions : ", 1, 12) == 8
    sortie = capsys.readouterr().out
    assert "entier" in sortie and "entre 1 et 12" in sortie
```

`monkeypatch` restaure tout après le test. Il remplace aussi des variables d'environnement (`monkeypatch.setenv`) ou des fonctions coûteuses (un appel réseau par un faux retour — indispensable aux chapitres 8-9).

Les fixtures partagées entre fichiers vivent dans `tests/conftest.py` (découvert automatiquement, aucun import nécessaire).

## 5. Que tester, et quoi d'abord

Priorités, dans l'ordre :

1. **La logique pure** (calculs, parsing, règles métier) : facile à tester, c'est là que vivent les bugs sournois. C'est pour ça qu'on a séparé `calculs.py` de la saisie au chapitre 4.
2. **Les frontières et les erreurs** : bornes exactes, entrées vides, exceptions attendues.
3. **La persistance** : round-trips (sauvegarder → charger → comparer) avec `tmp_path`.
4. L'interactif/l'affichage : en dernier, via monkeypatch/capsys — coût élevé, valeur moyenne.

Anti-patterns : tester les détails d'implémentation (le test casse à chaque refactoring), dépendre de l'ordre des tests, tests sans assert.

## 6. ruff et black : la qualité automatisée

- **black** formate le code, sans négociation : `black .` et l'affaire est close (fini les questions d'espaces du chapitre 0).
- **ruff** lint à grande vitesse : imports inutilisés, variables mortes, pièges classiques (mutable par défaut !), tri des imports. `ruff check .` (diagnostic), `ruff check --fix .` (corrections auto).

Configuration unique dans `pyproject.toml` à la racine :

```toml
[tool.black]
line-length = 88

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP"]   # pycodestyle, pyflakes, isort, bugbear, pyupgrade
```

Dans VS Code : extensions Ruff + Black Formatter, « Format on Save » activé — le style disparaît de tes préoccupations. (ruff sait aussi formater ; garder black + ruff-lint est un choix simple et courant.)

## 7. coverage : mesurer ce que les tests exécutent

```bash
pip install pytest-cov
python -m pytest --cov=entrainement --cov-report=term-missing
```

```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
entrainement/calculs.py      24      2    92%   31-32
```

`Missing` liste les lignes jamais exécutées par les tests — souvent les branches d'erreur. Vise ~80-90 % sur la logique métier ; 100 % n'est pas un objectif (le dernier décile coûte cher pour peu de valeur), et surtout : **la couverture mesure l'exécution, pas la justesse** — un test sans assert couvre tout et ne vérifie rien.

## Checklist de fin de chapitre

- [ ] J'écris des tests pytest (arrange/act/assert) et je les lance avec `python -m pytest`.
- [ ] Je teste les frontières et les exceptions (`pytest.raises`, `match=`).
- [ ] Je factorise les cas en tables avec `@pytest.mark.parametrize`.
- [ ] J'écris des fixtures (yield = setup/teardown) et j'utilise `tmp_path`, `capsys`, `monkeypatch`.
- [ ] ruff + black configurés dans pyproject.toml et branchés dans VS Code.
- [ ] Je lis un rapport de couverture et je sais ce qu'il ne dit pas.
