Ton app Cuisine devra interroger une API de recettes, ton app Finance plusieurs sources de cours. En séquentiel, 20 requêtes de 500 ms = 10 secondes d'attente... à ne rien faire : le programme dort en attendant le réseau. L'async fait autre chose pendant l'attente — 20 requêtes concurrentes ≈ le temps de la plus lente.

## 1. Le problème : I/O bound vs CPU bound

- **CPU bound** : le programme calcule (parsing lourd, agrégats). Pour aller plus vite : optimiser ou paralléliser sur plusieurs cœurs (multiprocessing — hors périmètre ici).
- **I/O bound** : le programme **attend** (réseau, disque, base). 99 % du temps d'une requête HTTP est de l'attente pure. C'est LE terrain de l'async.

L'async n'utilise qu'**un seul thread** : une boucle d'événements (*event loop*) fait tourner des coroutines qui **rendent la main** quand elles attendent. Pas de verrous, pas de course de threads : la concurrence est **coopérative** — une coroutine n'est interrompue qu'aux points `await` qu'elle a elle-même déclarés.

## 2. async / await : la mécanique

```python
import asyncio


async def fetch_cours(ticker: str) -> float:      # async def → coroutine
    await asyncio.sleep(0.5)                      # await : je rends la main ici
    return 100.0


async def main() -> None:
    cours = await fetch_cours("IWDA")             # attend le résultat
    print(cours)


asyncio.run(main())          # démarre la boucle : LE seul point d'entrée
```

Trois règles fondamentales :

- `async def` définit une **coroutine**. L'appeler (`fetch_cours("IWDA")`) ne l'exécute PAS : ça crée un objet coroutine. Seul `await` (ou la boucle) l'exécute. **Oublier `await` est le bug n°1** — souvent signalé par `RuntimeWarning: coroutine ... was never awaited`.
- `await` ne s'écrit que dans une fonction `async def`.
- `asyncio.run(main())` une seule fois, tout en haut. Le reste du programme vit dans la boucle.

Important : `await f()` **séquentialise** — la coroutine attend le résultat avant de continuer. Écrire trois `await` à la suite n'est pas plus rapide que du code synchrone. La concurrence vient de l'étape suivante.

## 3. asyncio.gather : la concurrence

```python
async def main() -> None:
    resultats = await asyncio.gather(
        fetch_cours("IWDA"),
        fetch_cours("EMIM"),
        fetch_cours("CSPX"),
    )
    # ~0.5 s au lieu de 1.5 s : les trois attentes se recouvrent
```

`gather` lance toutes les coroutines et attend qu'elles finissent toutes ; les résultats reviennent **dans l'ordre des arguments** (pas dans l'ordre d'achèvement). Avec une liste dynamique :

```python
taches = [fetch_cours(t) for t in tickers]
resultats = await asyncio.gather(*taches)          # * : déballe la liste
```

Par défaut, la première exception fait échouer le `gather` entier. Pour un lot où chaque élément peut échouer indépendamment :

```python
resultats = await asyncio.gather(*taches, return_exceptions=True)
# resultats mélange valeurs et objets exceptions → à trier soi-même
for ticker, res in zip(tickers, resultats):
    if isinstance(res, Exception):
        print(f"{ticker} : échec ({res})")
```

## 4. httpx.AsyncClient : le HTTP async

`httpx` a deux visages : `httpx.get(...)` synchrone (chapitre 9) et le client async :

```python
import httpx


async def fetch(client: httpx.AsyncClient, url: str) -> dict:
    reponse = await client.get(url)
    reponse.raise_for_status()             # lève sur 4xx/5xx
    return reponse.json()


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:   # UNE session partagée
        pages = await asyncio.gather(*(fetch(client, u) for u in urls))
```

- `async with` : le context manager version async (même logique que `with`, chapitre 5).
- **Un seul client pour toutes les requêtes** : il réutilise les connexions TCP (beaucoup plus rapide qu'un client par requête).
- **Toujours un timeout.** Le défaut de httpx est 5 s ; explicite-le. Sans timeout, une requête peut geler le programme indéfiniment.

## 5. Limiter la concurrence : Semaphore

Lancer 500 requêtes d'un coup sature ta machine et fait bannir ton IP (les API imposent des limites — chapitre 9). Le sémaphore plafonne le nombre de coroutines actives dans une section :

```python
sem = asyncio.Semaphore(5)                 # 5 requêtes simultanées max

async def fetch_poli(client, url):
    async with sem:                        # attend qu'un jeton se libère
        return await fetch(client, url)

resultats = await asyncio.gather(*(fetch_poli(client, u) for u in urls))
```

Les 20 tâches démarrent, mais seules 5 franchissent le sémaphore à la fois : les requêtes partent par vagues. C'est le pattern standard « concurrence bornée », à connaître par cœur.

## 6. Timeouts et annulation

Deux niveaux de timeout :

```python
# Par requête : le paramètre timeout du client (voir §4)

# Par opération globale :
try:
    async with asyncio.timeout(30):        # Python 3.11+
        resultats = await tout_recuperer()
except TimeoutError:
    print("le lot n'a pas fini en 30 s")
```

Quand un timeout expire, la coroutine reçoit une `CancelledError` à son prochain `await` : les `finally` et context managers s'exécutent (les ressources sont libérées proprement). C'est aussi ce qui se passe sur Ctrl+C — raison de plus pour tout mettre dans des `with`.

## 7. Les pièges

- **Code synchrone bloquant dans une coroutine** : `time.sleep(1)`, un gros calcul, `requests.get(...)` — tout ça **gèle la boucle entière** (aucune autre coroutine n'avance : elles ne reprennent qu'aux `await`). Dans une coroutine : `asyncio.sleep`, `httpx.AsyncClient`, et déporter les vrais calculs (`asyncio.to_thread` si nécessaire).
- **Oublier `await`** : la coroutine n'est jamais exécutée (warning à prendre au sérieux).
- **Sur-async-ifier** : un script qui fait 3 requêtes n'a pas besoin d'async. Le gain apparaît avec des dizaines d'I/O concurrentes. Ton code de calcul (Pandas, parsing) reste synchrone — l'async est une couche d'orchestration des I/O, pas un style de vie.

Note pour la suite : FastAPI (le moteur de cette application !) est construit sur asyncio — les routes `async def` de `main.py` sont des coroutines. Tout ce chapitre s'y applique directement.

## Checklist de fin de chapitre

- [ ] Je sais dire si un problème est I/O bound (async utile) ou CPU bound (async inutile).
- [ ] `async def` / `await` / `asyncio.run` : je connais le rôle exact de chacun et le bug du `await` oublié.
- [ ] Je parallélise avec `gather` (et `return_exceptions=True` pour les lots à échecs partiels).
- [ ] J'utilise UN `httpx.AsyncClient` partagé, avec timeout explicite.
- [ ] Je borne la concurrence avec un `Semaphore`.
- [ ] Je sais pourquoi `time.sleep` dans une coroutine est interdit, et ce qui se passe à l'annulation.
