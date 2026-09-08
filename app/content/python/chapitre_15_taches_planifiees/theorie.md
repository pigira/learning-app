Les cours d'ETF doivent se rafraîchir tout seuls, la base de recettes se synchroniser la nuit. Deux mécanismes distincts : la **tâche d'arrière-plan** (déclenchée par une requête, exécutée après la réponse) et la **tâche planifiée** (récurrente, pilotée par l'horloge). FastAPI fournit la première, APScheduler la seconde — et la fiabilité (erreurs, idempotence, journalisation) fait toute la différence entre un job de tutoriel et un job qui tourne six mois.

## 1. Deux besoins, deux outils

| Besoin | Déclencheur | Outil |
|---|---|---|
| « Réponds tout de suite, traite ensuite » | une requête HTTP | `BackgroundTasks` (FastAPI) |
| « Toutes les 15 min / chaque matin à 7 h » | l'horloge | APScheduler |
| Traitements lourds, distribués, avec reprise | file de messages | Celery/RQ — hors périmètre, à connaître de nom |

## 2. FastAPI BackgroundTasks

Une route qui importe un fichier de 50 Mo ne doit pas faire attendre le client. La réponse part, le travail suit :

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()


def importer_fichier(chemin: str) -> None:      # fonction ordinaire (ou async)
    ...                                          # le travail lent


@app.post("/imports")
async def lancer_import(chemin: str, taches: BackgroundTasks):
    taches.add_task(importer_fichier, chemin)   # planifié APRÈS la réponse
    return {"statut": "accepté"}                # part immédiatement (~ms)
```

Le client reçoit `202`-style « accepté » tout de suite ; `importer_fichier` s'exécute une fois la réponse envoyée. Limites à connaître : la tâche vit **dans le processus du serveur** — un redémarrage la tue, il n'y a ni file d'attente persistante ni retry automatique. Parfait pour : journalisation différée, envoi de notification, import ponctuel. Insuffisant pour : travail critique qui ne doit jamais se perdre (→ vraie file de jobs).

Le client ne sait pas quand ça finit : expose un état consultable (table `jobs_runs`, §6) plutôt que d'espérer.

## 3. APScheduler : les déclencheurs

```bash
pip install apscheduler
```

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler(timezone="Europe/Amsterdam")

scheduler.add_job(rafraichir_cours, IntervalTrigger(minutes=15),
                  id="refresh_cours", max_instances=1, coalesce=True)

scheduler.add_job(rapport_quotidien, CronTrigger(hour=7, minute=0),
                  id="rapport_matin")

scheduler.start()
```

- **`IntervalTrigger`** : toutes les N minutes/heures — pour le rafraîchissement continu.
- **`CronTrigger`** : à heure fixe (syntaxe cron : `hour=7`, `day_of_week="mon-fri"`) — pour les rendez-vous.
- **`timezone=\"Europe/Amsterdam\"`** explicite : sinon le « 7 h » dépend du réglage de la machine, et les changements d'heure été/hiver te réservent des surprises (un cron à 2 h 30 du matin ne s'exécute pas le jour du passage à l'heure d'été...).
- `id=` stable : permet de retrouver/modifier/annuler le job (`scheduler.get_job("refresh_cours")`).

Deux options qui évitent les ennuis classiques :

- **`max_instances=1`** : si le run précédent n'est pas fini quand l'heure sonne, ne PAS en lancer un deuxième en parallèle (le job de 15 min qui prend 20 min un jour de réseau lent → sans ça, les runs s'empilent).
- **`coalesce=True`** : si plusieurs exécutions ont été manquées (machine endormie), n'en rattraper qu'UNE au réveil, pas douze.

## 4. Intégration FastAPI : le lifespan

Le scheduler doit démarrer avec l'app et s'arrêter proprement avec elle — c'est exactement le rôle du `lifespan` (déjà croisé dans le moteur de cette application) :

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield                          # l'app tourne
    scheduler.shutdown(wait=True)  # arrêt propre : on laisse finir le run en cours


app = FastAPI(lifespan=lifespan)
```

Avec `AsyncIOScheduler`, les jobs `async def` tournent dans la même boucle que FastAPI — les règles du chapitre 8 s'appliquent telles quelles (pas de code bloquant dans un job async ; un gros calcul part dans `asyncio.to_thread`).

## 5. La fiabilité : erreurs, idempotence

**Un job qui lève une exception non gérée meurt en silence** — APScheduler logge et passe au tick suivant, personne ne le voit. Le squelette de tout job sérieux :

```python
import logging

logger = logging.getLogger("jobs")


async def rafraichir_cours() -> None:
    debut = datetime.now(timezone.utc)
    try:
        rapport = await collecter(tickers, base_url)      # chapitre 8
        upsert_cours(conn, rapport.cours)                 # chapitre 6
    except ApiIndisponible as exc:                        # chapitre 9
        logger.warning("refresh_cours : source indisponible (%s) — retick dans 15 min", exc)
        enregistrer_run("refresh_cours", debut, "echec", str(exc))
        return                                            # le PROCHAIN tick réessaiera
    except Exception:
        logger.exception("refresh_cours : erreur inattendue")   # traceback complète
        enregistrer_run("refresh_cours", debut, "erreur", "voir logs")
        raise
    enregistrer_run("refresh_cours", debut, "ok", f"{len(rapport.cours)} cours")
```

Deux principes :

- **L'échec attendu** (API down) se logge et s'abandonne : le job périodique EST le mécanisme de retry — inutile d'empiler des retries dans le job par-dessus ceux du client HTTP.
- **L'idempotence est obligatoire** : le job peut tourner deux fois (rattrapage, redémarrage, run manuel) — grâce à l'**upsert** du chapitre 6 (`ON CONFLICT ... DO UPDATE`), le double run produit exactement le même état. Un job à base d'`INSERT` nus double les données au premier incident. Test à faire systématiquement : lancer le job deux fois de suite, vérifier que l'état est identique.

## 6. Journaliser les runs : la table jobs_runs

Les logs défilent, une table reste. Chaque exécution s'enregistre :

```sql
CREATE TABLE IF NOT EXISTS jobs_runs (
    id      INTEGER PRIMARY KEY,
    job     TEXT NOT NULL,
    debut   TEXT NOT NULL,           -- ISO UTC
    fin     TEXT,
    statut  TEXT NOT NULL,           -- ok | echec | erreur
    detail  TEXT
);
```

Ce petit investissement paie trois fois : un endpoint `GET /statut` peut afficher « dernier refresh : il y a 4 min, OK » ; le debugging d'un trou de données remonte au run fautif ; et le cron quotidien peut vérifier « ai-je déjà tourné aujourd'hui ? » (`SELECT ... WHERE job = ? AND date(debut) = date('now')`) — l'exécution-unique-par-jour devient une requête, pas un espoir.

Le logging applicatif accompagne (module `logging`, niveau INFO pour les runs, WARNING pour les échecs attendus, `logger.exception` pour l'imprévu) — jamais de `print` dans un job : on veut l'horodatage et le niveau.

## 7. Récapitulatif des pièges

| Piège | Parade |
|---|---|
| Job qui meurt en silence | try/except + logging + table jobs_runs |
| Runs qui s'empilent | `max_instances=1` |
| Rattrapage en rafale après veille | `coalesce=True` |
| Doublons de données au re-run | upsert idempotent (chapitre 6) |
| « 7 h » qui dérive | timezone explicite Europe/Amsterdam |
| Job bloquant qui gèle l'API | règles async du chapitre 8 (`to_thread`) |
| Travail critique perdu au redémarrage | ce n'est plus un job in-process → vraie file (Celery) |

## Checklist de fin de chapitre

- [ ] Je choisis correctement entre BackgroundTasks (déclenché) et APScheduler (récurrent), et je connais leurs limites.
- [ ] Je configure interval et cron avec timezone explicite, `max_instances=1`, `coalesce=True`.
- [ ] Mon scheduler démarre et s'arrête via le lifespan FastAPI.
- [ ] Tout job a son try/except : échec attendu loggé et abandonné, imprévu tracé avec `logger.exception`.
- [ ] Mes jobs sont idempotents (upsert) — testé en les lançant deux fois.
- [ ] Chaque run laisse une trace en base (jobs_runs), consultable par un endpoint /statut.
