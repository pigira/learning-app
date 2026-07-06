« Ça marche sur ma machine » n'est pas une livraison. Docker empaquette ton app AVEC son environnement (Python, dépendances, config) dans une **image** qui tourne à l'identique partout — ta machine, un serveur, le cloud. Ce chapitre te fait dockeriser une app FastAPI + SQLite, avec volumes pour les données et docker-compose pour l'orchestration. C'est l'étape de déploiement de tes trois projets.

## 1. Images, conteneurs, layers

Le vocabulaire, précis :

- **Image** : un modèle figé et immuable — ton code + Python + les dépendances + la config de démarrage. On la construit une fois.
- **Conteneur** : une instance en cours d'exécution d'une image (comme un objet est une instance de classe). Jetable : on en lance, on en tue, l'image reste.
- **Layer** : une image est faite de couches empilées, une par instruction du Dockerfile. Docker les **met en cache** — d'où l'importance de leur ordre (§2).
- **Registry** : un dépôt d'images (Docker Hub, Azure Container Registry). `pull` pour récupérer, `push` pour publier.

Installation sur macOS : **Docker Desktop** (`brew install --cask docker`, puis lancer l'app). `docker --version` et `docker run hello-world` confirment.

Différence avec une VM : un conteneur partage le noyau de l'hôte (léger, démarrage en ~1 s), une VM émule une machine complète (lourde). Pour livrer une app, le conteneur est l'outil.

## 2. Le Dockerfile Python

Le `Dockerfile` décrit la construction de l'image, instruction par instruction :

```dockerfile
FROM python:3.12-slim                    # image de base légère

WORKDIR /app                             # dossier de travail dans le conteneur

# Les dépendances D'ABORD (layer mis en cache tant que requirements ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Le code ENSUITE (change souvent → ne réinvalide pas le layer des dépendances)
COPY . .

EXPOSE 8000                              # documentation du port (n'ouvre rien)

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Les décisions qui comptent :

- **`python:3.12-slim`** : la variante « slim » (Debian minimal) pèse ~150 Mo contre ~1 Go pour l'image complète — assez pour la plupart des projets. (`alpine` est encore plus petit mais pose des soucis avec les paquets compilés comme pandas : slim est le bon défaut.)
- **L'ordre requirements → code est LA optimisation clé** : Docker rebuild à partir du premier layer modifié. En copiant `requirements.txt` et en installant AVANT de copier le code, une simple modification de code ne réinstalle PAS les dépendances (cache réutilisé) — build de quelques secondes au lieu de minutes.
- **`--host 0.0.0.0`** : dans un conteneur, écouter sur `127.0.0.1` rendrait l'app injoignable de l'extérieur du conteneur. `0.0.0.0` écoute sur toutes les interfaces.
- **`CMD` en forme JSON** (`["...", "..."]`) : la commande de démarrage du conteneur.

## 3. .dockerignore et utilisateur non-root

Deux réflexes d'hygiène :

```
# .dockerignore — comme .gitignore, mais pour le build
.venv/
__pycache__/
*.pyc
.env
.git/
data/*.db
```

`.dockerignore` évite de copier dans l'image le venv local (inutile, lourd), les secrets (`.env` !), la base de données, l'historique git. Sans lui, `COPY . .` embarque tout — y compris ce qui ne doit jamais s'y trouver.

**Utilisateur non-root** : par défaut un conteneur tourne en root — si l'app est compromise, l'attaquant est root dans le conteneur. On crée un utilisateur dédié :

```dockerfile
RUN useradd --create-home appuser
USER appuser
```

## 4. Construire et lancer

```bash
docker build -t enduro-app .              # construit l'image, tag "enduro-app"
docker run -p 8000:8000 enduro-app        # lance ; -p HÔTE:CONTENEUR mappe le port

docker run -d --name enduro enduro-app    # -d : en arrière-plan (détaché)
docker logs -f enduro                     # suivre les logs
docker exec -it enduro bash               # ouvrir un shell dans le conteneur
docker stop enduro && docker rm enduro    # arrêter et supprimer
```

`-p 8000:8000` : le port 8000 de ta machine est redirigé vers le 8000 du conteneur (l'app y devient accessible sur `localhost:8000`). Sans ce mapping, le conteneur est isolé.

## 5. Configuration par variables d'environnement

Un conteneur reçoit sa config par variables d'environnement — et c'est exactement ce que pydantic-settings (chapitre 14) attend, avec la bonne précédence (l'environnement bat le `.env`) :

```bash
docker run -p 8000:8000 \\
  -e APP_ENV=prod \\
  -e API_COURS__CLE=sk-reelle \\
  --env-file .env.prod \\
  enduro-app
```

`-e` injecte une variable, `--env-file` charge un fichier entier. Ta classe `Settings` les lit sans AUCUNE modification de code — le même code tourne en dev (`.env.dev`) et en conteneur prod (variables injectées). C'est la promesse 12-factor du chapitre 14, réalisée. Les secrets n'entrent JAMAIS dans l'image (d'où `.env` dans `.dockerignore`) : ils sont injectés au lancement.

## 6. Volumes : les données qui survivent

Un conteneur est **jetable** : tout ce qu'il écrit disparaît quand on le supprime. Ta base SQLite doit donc vivre dans un **volume** — un stockage persistant monté dans le conteneur :

```bash
docker run -p 8000:8000 -v enduro-data:/app/data enduro-app
#                          └ volume nommé    └ chemin DANS le conteneur
```

Le dossier `/app/data` du conteneur (où vit `progress.db`) pointe vers le volume `enduro-data` sur l'hôte. Détruire et relancer le conteneur : la base est intacte. Sans `-v`, chaque `docker rm` efface les données.

Deux types de montage : les **volumes nommés** (gérés par Docker, pour les données de prod) et les **bind mounts** (`-v $(pwd)/data:/app/data`, un dossier de l'hôte — pratique en dev pour voir les fichiers, ou pour monter le contenu pédagogique de cette app sans rebuild).

## 7. docker-compose : orchestrer

Taper de longues commandes `docker run` est pénible et non reproductible. `docker-compose.yml` décrit l'app entière — services, ports, volumes, config — en un fichier versionné :

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.prod
    volumes:
      - enduro-data:/app/data
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/')"]
      interval: 30s
      retries: 3

  worker:                                 # le service de refresh (chapitre 15)
    build: .
    command: python -m enduro.worker
    env_file:
      - .env.prod
    volumes:
      - enduro-data:/app/data             # MÊME volume : base partagée
    depends_on:
      - api

volumes:
  enduro-data:
```

```bash
docker compose up -d          # construit et lance tous les services
docker compose logs -f        # logs de tout
docker compose down           # arrête tout (les volumes SURVIVENT)
docker compose down -v        # ... et supprime les volumes (données perdues)
```

Points utiles : `depends_on` ordonne le démarrage ; `healthcheck` permet à Docker de savoir si un service est vraiment prêt (pas juste « démarré ») ; deux services partageant un volume partagent la base (l'API sert, le worker rafraîchit — ton projet du chapitre 15).

## 8. Diagnostic

| Symptôme | Piste |
|---|---|
| App injoignable | `--host 0.0.0.0` ? port mappé `-p` ? |
| Données perdues au redémarrage | volume manquant (`-v`) |
| Build lent à chaque fois | ordre requirements/code dans le Dockerfile |
| Image énorme (>1 Go) | base non-slim, `.dockerignore` absent |
| « module not found » | dépendance absente de requirements.txt |
| Secret dans l'image | `.env` non ignoré → à corriger d'urgence |

`docker logs`, `docker exec -it ... bash` (explorer le conteneur vivant), `docker inspect` (config détaillée), `docker images` / `docker ps` sont tes outils.

## Checklist de fin de chapitre

- [ ] Je distingue image / conteneur / layer / volume et j'installe Docker Desktop.
- [ ] J'écris un Dockerfile Python correct (slim, ordre requirements→code, host 0.0.0.0, non-root).
- [ ] `.dockerignore` exclut venv, `.env`, la base, git.
- [ ] Je build, run (`-p`, `-d`), consulte les logs, entre dans le conteneur.
- [ ] Je configure par variables d'environnement (compatibles pydantic-settings) — secrets injectés, jamais dans l'image.
- [ ] Ma base SQLite vit dans un volume et survit à la destruction du conteneur.
- [ ] J'orchestre avec docker-compose (services, volume partagé, healthcheck, depends_on).
