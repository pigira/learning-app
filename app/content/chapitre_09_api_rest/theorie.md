Tes apps Cuisine et Finance vivront de données externes : recettes, cours d'ETF. Ce chapitre professionnalise la consommation d'API REST : le protocole HTTP tel qu'il se pratique, l'authentification, et les trois réalités que les tutoriels ignorent — pagination, rate limiting, pannes réseau.

## 1. Anatomie d'un échange HTTP

Une requête = un **verbe**, une **URL**, des **headers**, éventuellement un **corps**. Une réponse = un **code de statut**, des headers, un corps (JSON dans 95 % des cas modernes).

| Verbe | Usage | Idempotent ? |
|---|---|---|
| GET | lire | oui (rejouable sans danger) |
| POST | créer / actions | non |
| PUT / PATCH | remplacer / modifier | oui / souvent |
| DELETE | supprimer | oui |

Codes de statut, par famille : **2xx** succès (200 OK, 201 Created, 204 No Content) ; **4xx** erreur CLIENT — c'est TA requête qui est en cause (400 malformée, 401 non authentifié, 403 interdit, 404 introuvable, 422 invalide, **429 trop de requêtes**) ; **5xx** erreur SERVEUR (500, 502/503 indisponible). La distinction 4xx/5xx pilote la stratégie de retry (§6) : retenter un 404 est absurde, retenter un 503 est raisonnable.

## 2. httpx : la pratique

```python
import httpx

reponse = httpx.get(
    "https://www.themealdb.com/api/json/v1/1/filter.php",
    params={"i": "chicken"},              # → ?i=chicken (encodage géré)
    timeout=10.0,                         # TOUJOURS
)
reponse.raise_for_status()                # lève httpx.HTTPStatusError sur 4xx/5xx
donnees = reponse.json()                  # dict/list depuis le corps JSON
```

- `params=` construit la query string proprement (espaces, accents encodés) — ne concatène jamais à la main.
- `raise_for_status()` systématique : sans lui, un 500 renvoie tranquillement son HTML d'erreur à ton `json()` qui explose plus loin, hors contexte.
- `reponse.status_code`, `reponse.headers`, `reponse.text` pour inspecter.
- POST JSON : `httpx.post(url, json={"nom": "..."})` (le header `Content-Type` est géré).

Pour plusieurs requêtes vers la même API, un **client réutilisable** :

```python
with httpx.Client(base_url="https://api.example.com", timeout=10.0,
                  headers={"User-Agent": "mon-app/0.1"}) as client:
    r1 = client.get("/recettes", params={"q": "pasta"})
    r2 = client.get("/recettes/42")
```

Connexions TCP réutilisées, configuration centralisée. (La version async — `AsyncClient` — est au chapitre 8 ; tout ce chapitre s'applique aux deux.)

## 3. Authentification

Trois schémas couvrent l'essentiel :

```python
# 1. API key — en header (préférable) ou en query param (selon la doc de l'API)
client = httpx.Client(headers={"X-API-Key": settings.api_key})

# 2. Bearer token — le standard de facto
client = httpx.Client(headers={"Authorization": f"Bearer {token}"})

# 3. OAuth2 client_credentials — échanger des identifiants contre un token
reponse = httpx.post("https://auth.example.com/oauth/token", data={
    "grant_type": "client_credentials",
    "client_id": settings.client_id,
    "client_secret": settings.client_secret,
})
token = reponse.json()["access_token"]     # souvent muni d'une expiration
```

OAuth2 complet (avec navigateur et consentement utilisateur) suit la même idée — un token temporaire obtenu via un flux — mais tes projets utiliseront surtout API key et Bearer. Règles non négociables : la clé vient de la configuration (variable d'environnement — formalisé au chapitre 14), **jamais** dans le code, jamais dans les logs, jamais côté client web (chapitre 19). Un 401 = token absent/expiré ; un 403 = authentifié mais pas autorisé.

## 4. Pagination

Aucune API sérieuse ne renvoie 10 000 éléments d'un coup. Deux styles :

**Offset/limit** (`?offset=40&limit=20`) — simple, mais fragile si les données bougent entre deux pages.

**Curseur** : chaque réponse contient l'URL ou le jeton de la page suivante — c'est le style PokeAPI (`"next": "https://...?offset=20"`) ou GitHub (header `Link`).

Le pattern universel côté client est le **générateur** qui masque la pagination :

```python
def tous_les_elements(client: httpx.Client, url: str):
    while url:
        reponse = client.get(url)
        reponse.raise_for_status()
        page = reponse.json()
        yield from page["results"]        # livre les éléments un à un
        url = page.get("next")            # None → fin de la boucle

for element in tous_les_elements(client, premiere_page):   # l'appelant itère,
    ...                                                      # les pages sont invisibles
```

`yield` fait de la fonction un générateur : elle produit les éléments à la demande, page par page — mémoire constante, et l'appelant peut s'arrêter quand il veut (les pages suivantes ne seront jamais demandées).

## 5. Rate limiting

Les API limitent le débit (ex. 60 requêtes/minute). Au-delà : **429 Too Many Requests**, souvent avec le header `Retry-After: 17` (secondes à attendre). Bien se comporter :

- **Préventif** : borner sa concurrence (Semaphore, chapitre 8) et espacer les lots.
- **Réactif** : sur 429, respecter `Retry-After` s'il est présent, sinon backoff exponentiel (§6).
- Ignorer un 429 et marteler = ban d'IP ou de clé. Le rate limiting n'est pas un obstacle, c'est le contrat.

## 6. Erreurs réseau et retries

Trois familles d'échec, trois traitements :

| Échec | Exemple httpx | Retenter ? |
|---|---|---|
| Erreur réseau (pas de réponse) | `httpx.ConnectError`, `httpx.TimeoutException` | oui |
| Erreur serveur (5xx) | `HTTPStatusError` avec status ≥ 500 | oui |
| Erreur client (4xx) | `HTTPStatusError` 400/401/404/422 | **non** — corriger la requête |

Le **backoff exponentiel avec jitter** est le standard : attendre 1 s, 2 s, 4 s... avec une part d'aléa (le jitter évite que tous les clients retentent au même instant) :

```python
import random
import time


def get_avec_retry(client: httpx.Client, url: str, essais: int = 4, **kwargs) -> httpx.Response:
    for essai in range(essais):
        try:
            reponse = client.get(url, **kwargs)
            if reponse.status_code == 429:
                attente = float(reponse.headers.get("Retry-After",
                                                     2 ** essai + random.random()))
                time.sleep(attente)
                continue
            if reponse.status_code >= 500:
                raise httpx.HTTPStatusError("5xx", request=reponse.request,
                                            response=reponse)
            reponse.raise_for_status()      # 4xx restants : remonte sans retry
            return reponse
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            est_4xx = (isinstance(exc, httpx.HTTPStatusError)
                       and exc.response.status_code < 500)
            if est_4xx or essai == essais - 1:
                raise
            time.sleep(2 ** essai + random.random())
    raise RuntimeError("inatteignable")
```

Attention : ne retenter que des opérations **idempotentes** (GET, PUT, DELETE). Retenter un POST « créer une commande » après un timeout peut créer deux commandes — le timeout ne dit pas si le serveur a traité ou non la première.

## 7. Concevoir un client réutilisable

Toutes ces préoccupations (base_url, auth, timeout, retry, pagination, erreurs) se rangent dans **une classe client**, pour que le reste de l'application parle métier :

```python
class ClientRecettes:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    def par_ingredient(self, ingredient: str) -> list[Recette]:
        ...   # requête + retry + normalisation + exceptions métier

    def close(self) -> None:
        self._client.close()
```

Deux principes : **normaliser tôt** (le JSON baroque de l'API est converti en TES dataclasses dès la frontière — le reste du code ne voit jamais le format externe) ; **exceptions métier** (`RecetteApiIndisponible`, pas `httpx.ConnectError` qui fuit dans toute l'application). C'est le projet de ce chapitre.

## Checklist de fin de chapitre

- [ ] Je lis un échange HTTP (verbe, statut, headers) et je sais ce que 401/403/404/422/429/503 impliquent pour MON code.
- [ ] `params=`, `timeout=`, `raise_for_status()` : mes trois réflexes httpx.
- [ ] Je m'authentifie par API key / Bearer, clé toujours hors du code.
- [ ] J'écris un générateur de pagination qui masque les pages à l'appelant.
- [ ] Je gère le 429 (Retry-After) et je retente avec backoff+jitter — uniquement ce qui doit l'être.
- [ ] Mes appels d'API vivent dans une classe client qui normalise vers mes dataclasses et lève des exceptions métier.
