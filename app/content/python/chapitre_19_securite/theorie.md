Tes trois apps manipulent des entrées externes (formulaires, API, uploads de `.fit`), des secrets (clés API) et une base de données. Ce chapitre installe les réflexes de sécurité minimum — ni exhaustif ni paranoïaque, mais les quelques barrières qui écartent les erreurs qui font vraiment mal : injection, secrets exposés, XSS, uploads piégés.

## 1. Le modèle de menace d'une app perso

Avant de se défendre, savoir contre quoi. Une app locale ou perso n'a pas les menaces d'une banque, mais elle en a de réelles :

- **Tes propres erreurs** deviennent des failles : un SQL en f-string, une clé dans git, une page qui affiche du HTML non échappé.
- **Les données externes sont hostiles par défaut** : une réponse d'API, un fichier `.fit`, un texte collé dans un prompt LLM — rien de ce qui vient de l'extérieur n'est digne de confiance tant qu'il n'est pas validé.
- Si l'app est un jour exposée sur le réseau (démo, déploiement), la surface s'élargit : tout endpoint devient atteignable.

Principe directeur : **ne jamais faire confiance à une entrée**, et **garder les secrets côté serveur**. Le reste en découle.

## 2. Validation des entrées : Pydantic comme douane

Toute donnée qui entre (corps de requête, paramètres, fichier, réponse d'API, argument d'outil LLM) passe par une validation. Pydantic (chapitres 14, 17) est la douane :

```python
from pydantic import BaseModel, Field, field_validator


class RecetteEntree(BaseModel):
    model_config = {"extra": "forbid"}      # rejette tout champ non déclaré

    nom: str = Field(min_length=1, max_length=120)
    temps_min: int = Field(ge=1, le=1440)
    portions: int = Field(ge=1, le=50)

    @field_validator("nom")
    @classmethod
    def _pas_de_controle(cls, v: str) -> str:
        if any(c in v for c in "\\x00\\r\\n"):
            raise ValueError("caractères de contrôle interdits")
        return v.strip()
```

Dans FastAPI, une entrée typée par ce modèle est validée automatiquement — une requête non conforme reçoit un `422` avant d'atteindre ta logique. Les leviers : bornes (`ge/le`, `min_length/max_length`), `extra="forbid"` (pas de champ surprise), validateurs custom, et une **limite de taille** sur les payloads (un JSON de 2 Go est une attaque par déni de service).

## 3. Injection SQL

La faille classique, et la plus facile à éviter. Elle survient quand une entrée est **concaténée** dans une requête :

```python
# CATASTROPHE — n'écris JAMAIS ça
nom = request["nom"]
cur.execute(f"SELECT * FROM recettes WHERE nom = '{nom}'")
# avec nom = "x'; DROP TABLE recettes; --" → ta table disparaît
```

La parade est unique et absolue : **requêtes paramétrées** (chapitre 6). Le `?` sépare le CODE SQL (fixe) des DONNÉES (variables), et le driver échappe correctement :

```python
cur.execute("SELECT * FROM recettes WHERE nom = ?", (nom,))     # sûr, toujours
cur.execute("SELECT * FROM cours WHERE ticker = ? AND jour = ?", (ticker, jour))
```

Ce qui ne marche PAS et qu'il faut bannir : l'échappement manuel (`nom.replace("'", "''")` — mille cas particuliers), les « listes blanches de caractères », faire confiance parce que « l'entrée vient de mon front ». Un nom de table ou de colonne dynamique (qui ne peut pas être un `?`) se valide contre une **liste blanche en dur** (`if colonne not in COLONNES_AUTORISEES: raise`), jamais par interpolation. Règle mentale : **zéro donnée dans le texte d'une requête, point.**

## 4. XSS : l'injection côté navigateur

Symétrique de l'injection SQL, côté affichage : si tu insères une entrée utilisateur dans une page HTML sans l'échapper, un `<script>` fourni par l'utilisateur s'exécute chez les autres visiteurs.

- **Templates Jinja2** (le moteur de cette application) : l'auto-échappement est **actif par défaut** — `{{ nom }}` transforme `<script>` en texte inoffensif. Le danger vient du contournement volontaire : `{{ contenu | safe }}` ou `render` de HTML brut désactive la protection. N'utilise `| safe` que sur du contenu que TU as produit (le Markdown rendu de cette app est un cas limite assumé et contrôlé).
- **Côté JavaScript** : `element.textContent = donnee` (sûr) vs `element.innerHTML = donnee` (injecte du HTML — dangereux avec une donnée externe). Préfère `textContent` ; réserve `innerHTML` à du HTML que tu maîtrises.

Le principe est le même qu'en SQL : séparer le code (structure HTML) des données (contenu), et laisser l'outil échapper.

## 5. Secrets : la règle d'or côté serveur

Repris des chapitres 9 et 14, parce que c'est la faille la plus courante en pratique :

- **Jamais dans le code, jamais dans git** : `.env` gitignoré, `SecretStr`, `.env.example` versionné. Une clé poussée = une clé morte (rotation immédiate).
- **Jamais côté client** : une clé API dans du JavaScript de navigateur est PUBLIQUE (visible dans les DevTools, le source de la page). Le pattern correct : le front appelle TON backend, qui détient la clé et **proxifie** l'appel externe.

```
Navigateur → TON backend (détient la clé) → API externe
             ^ la clé ne quitte jamais le serveur
```

C'est la raison d'être du client API du chapitre 9 côté serveur : il porte le secret, le front ne voit que tes endpoints.

## 6. CORS : qui peut appeler ton API depuis un navigateur

CORS (Cross-Origin Resource Sharing) contrôle quels sites web peuvent appeler ton API depuis le navigateur d'un utilisateur. Trop permissif = n'importe quel site peut piloter ton API avec les sessions de tes utilisateurs.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # TES origines, énumérées
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

L'anti-pattern à connaître : `allow_origins=["*"]` combiné à des credentials — copié de tutoriels, il ouvre l'API à tout le web. Énumère tes origines réelles. Pour une app 100 % locale servie par le même FastAPI (comme celle-ci), CORS ne se pose même pas : tout est même origine.

## 7. Uploads et traversée de chemin

Tes `.fit` (chapitre 16) et CSV arrivent par upload — terrain à risques :

```python
from pathlib import Path

STOCKAGE = Path("data/uploads").resolve()


def sauver_upload(nom_fourni: str, contenu: bytes) -> Path:
    if len(contenu) > 10 * 1024 * 1024:            # 1. taille max (anti-DoS)
        raise ValueError("fichier trop volumineux")
    if Path(nom_fourni).suffix.lower() not in {".fit", ".csv"}:   # 2. extension
        raise ValueError("type non autorisé")

    cible = (STOCKAGE / Path(nom_fourni).name).resolve()   # 3. .name retire tout chemin
    if cible.parent != STOCKAGE:                            # 4. anti-traversée
        raise ValueError("chemin invalide")
    cible.write_bytes(contenu)
    return cible
```

Les quatre défenses : taille bornée (un upload de 5 Go = déni de service) ; extension validée ; `Path(nom).name` qui neutralise un nom piégé comme `../../etc/passwd` (garde juste `passwd`) ; et la vérification finale que le chemin résolu reste bien dans le dossier autorisé. Bonus : stocker sous un nom **généré** (uuid) plutôt que le nom fourni élimine toute une classe de problèmes. La validation d'extension ne garantit pas le contenu — le parsing (fitparse) reste ta vraie ligne de défense sur ce qu'il y a DANS le fichier.

Note : cette application vérifie déjà la traversée de chemin dans `content.py` (`obtenir_chapitre` refuse un slug qui sortirait de `CONTENT_DIR`) — relis-le avec l'œil de ce chapitre.

## 8. Dépendances et hygiène continue

Le code que tu n'as pas écrit peut aussi être vulnérable :

- `pip-audit` (ou `pip install ... --report`) signale les dépendances à failles connues (CVE). À lancer régulièrement et avant un déploiement.
- Épingler les versions (`requirements.txt` gelé, chapitre 0) pour des builds reproductibles, et les mettre à jour en conscience.
- `gitleaks` (chapitre 14) avant de rendre un dépôt public.

## Checklist de fin de chapitre

- [ ] Je valide toute entrée externe avec Pydantic (bornes, `extra="forbid"`, taille max).
- [ ] Zéro donnée dans le texte d'une requête SQL — requêtes paramétrées partout.
- [ ] Je compte sur l'auto-échappement Jinja2 et j'utilise `| safe` / `innerHTML` en connaissance de cause.
- [ ] Mes secrets restent côté serveur ; le front passe par mon backend (proxy), jamais par la clé directe.
- [ ] CORS configuré avec des origines énumérées, jamais `*` + credentials.
- [ ] Mes uploads sont bornés en taille, validés en extension, protégés contre la traversée de chemin.
- [ ] Je lance `pip-audit` et `gitleaks` avant de publier.
