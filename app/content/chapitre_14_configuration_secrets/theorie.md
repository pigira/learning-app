Tes trois projets vont accumuler des clés : API de recettes, source de cours, Azure OpenAI. Une clé dans le code = une clé dans git = une clé publique (les scanners de dépôts trouvent une clé fraîchement poussée en quelques minutes). Ce chapitre installe la discipline définitive : **toute configuration hors du code**, validée au démarrage par `pydantic-settings`.

## 1. Le principe : le code est public, la config est locale

Règle des [12-factor apps](https://12factor.net/fr/config), à appliquer même en solo : le MÊME code doit pouvoir tourner en dev et en prod — seule la configuration change (URLs, clés, timeouts, flags). Corollaire : si une valeur devait changer entre deux environnements ou ne doit pas apparaître dans git, elle n'a rien à faire dans un `.py`.

Test mental : « je publie ce dépôt sur GitHub demain » — qu'est-ce qui doit en sortir ? Clés, tokens, chemins personnels, URLs internes.

## 2. Variables d'environnement

Le canal standard de la config :

```bash
export API_RECETTES_CLE="sk-abc123"      # dans le shell courant
API_RECETTES_CLE="sk-abc123" python3 app.py   # pour UNE commande
```

```python
import os

cle = os.environ["API_RECETTES_CLE"]        # KeyError si absente → échec au démarrage
cle = os.environ.get("API_RECETTES_CLE")    # None si absente → à toi de gérer
```

Échouer **au démarrage** si une clé manque est le bon comportement : mieux vaut un crash immédiat et clair qu'un appel d'API qui échoue trois heures plus tard dans un job de nuit.

## 3. `.env` : les variables en fichier

Exporter à la main est pénible ; le fichier `.env` à la racine du projet regroupe tout :

```bash
# .env — JAMAIS versionné
APP_ENV=dev
API_RECETTES_CLE=sk-abc123
AZURE_OPENAI_ENDPOINT=https://mon-instance.openai.azure.com
AZURE_OPENAI_KEY=xyz789
DB_CHEMIN=data/app.db
```

Deux compagnons obligatoires :

- **`.gitignore`** contient `.env` — à vérifier AVANT le premier commit du fichier.
- **`.env.example`** versionné : les mêmes clés avec des valeurs bidon (`API_RECETTES_CLE=changez-moi`) — la documentation vivante de ce que l'app attend. Nouveau poste de travail : `cp .env.example .env` et remplir.

`python-dotenv` charge ce fichier, mais tu n'en auras pas besoin directement : pydantic-settings le fait.

## 4. pydantic-settings : la config typée et validée

```bash
pip install pydantic-settings
```

La configuration devient une classe — types, défauts, validation, chargement automatique de l'environnement et du `.env` :

```python
from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "dev"
    db_chemin: str = "data/app.db"

    api_recettes_url: HttpUrl = HttpUrl("https://www.themealdb.com/api/json/v1/1")
    api_recettes_cle: SecretStr                      # OBLIGATOIRE : pas de défaut
    timeout_s: float = Field(default=10.0, gt=0, le=120)

    azure_openai_endpoint: HttpUrl
    azure_openai_key: SecretStr


settings = Settings()      # lit os.environ PUIS .env (l'environnement gagne)
```

Ce qu'on gagne sur `os.environ.get` :

- **Types convertis et validés** : `TIMEOUT_S=abc` ou `timeout_s=-5` → erreur explicite AU DÉMARRAGE, qui liste tous les champs fautifs d'un coup.
- **Champs obligatoires** : `api_recettes_cle` sans valeur → `ValidationError: Field required` — impossible de démarrer à moitié configuré.
- **Le mapping est automatique** : le champ `api_recettes_cle` lit la variable `API_RECETTES_CLE` (insensible à la casse).
- **`HttpUrl`, `Field(gt=0)`** : la validation métier de la config elle-même.

## 5. SecretStr : les secrets qui ne fuient pas

```python
print(settings.api_recettes_cle)           # **********
print(f"{settings=}")                      # les secrets restent masqués
settings.api_recettes_cle.get_secret_value()   # la vraie valeur — appel EXPLICITE
```

`SecretStr` masque la valeur dans `repr`, `str`, et donc dans les logs, les messages d'erreur, les traceback affichées. La fuite accidentelle (un `print(settings)` de debug, une erreur loggée) devient inoffensive. Le `.get_secret_value()` explicite se greppe facilement : tu sais exactement où tes secrets sont consommés.

```python
client = httpx.Client(headers={
    "X-API-Key": settings.api_recettes_cle.get_secret_value()
})
```

## 6. Multi-environnements

Un fichier par environnement, sélectionné par une variable :

```python
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f".env.{os.environ.get('APP_ENV', 'dev')}",
    )
```

```bash
python3 app.py                    # lit .env.dev
APP_ENV=prod python3 app.py       # lit .env.prod
```

`.env.dev` pointe vers une base jetable et des API de test ; `.env.prod` vers le vrai. Les DEUX restent hors git (seul `.env.example` est versionné). En dev, des défauts raisonnables dans la classe permettent de démarrer sans rien configurer — les champs SecretStr obligatoires forcent uniquement ce qui doit l'être.

## 7. Le point d'accès unique : get_settings()

Instancier `Settings()` partout relirait le `.env` à chaque fois et compliquerait les tests. Le pattern standard :

```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Tout le code appelle `get_settings()` : une seule instance (le cache), importable partout, et **remplaçable dans les tests** (`get_settings.cache_clear()` + monkeypatch des variables d'environnement, ou injection d'un `Settings(api_recettes_cle=SecretStr("test"))` construit à la main). FastAPI l'utilise via `Depends(get_settings)` — même pattern.

## 8. Hygiène opérationnelle

- **Clé compromise (poussée dans git, collée dans un chat)** : la **révoquer immédiatement** chez le fournisseur et en générer une autre. Supprimer le commit ne suffit JAMAIS (forks, caches, scanners l'ont déjà). La rotation est la seule réponse.
- **Scanner son dépôt** : [gitleaks](https://github.com/gitleaks/gitleaks) détecte les secrets dans l'historique (`gitleaks detect`) — à lancer avant de rendre un dépôt public.
- **Azure en particulier** : préfère les identités managées / `DefaultAzureCredential` quand le code tourne dans Azure (aucune clé à gérer du tout) ; les clés dans `.env` restent pour le dev local. Key Vault est l'étage au-dessus pour les équipes.
- Les logs : ne jamais logger une config complète non plus — SecretStr te protège, mais pas si tu logges `os.environ`.

## Checklist de fin de chapitre

- [ ] Plus aucune valeur d'environnement (clé, URL, chemin, flag) dans mes `.py`.
- [ ] `.env` gitignoré + `.env.example` versionné et à jour : le duo est en place dans chaque projet.
- [ ] Ma classe `Settings` valide types et bornes, et refuse de démarrer incomplète.
- [ ] Tous les secrets sont des `SecretStr`, consommés via `get_secret_value()` explicite.
- [ ] `get_settings()` avec `lru_cache` est le point d'accès unique, testable.
- [ ] Je sais quoi faire d'une clé compromise (rotation immédiate) et scanner un dépôt avant publication.
