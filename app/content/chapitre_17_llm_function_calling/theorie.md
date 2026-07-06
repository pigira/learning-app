L'app Cuisine doit comprendre « qu'est-ce que je peux cuisiner ce soir avec des œufs, en moins de 20 minutes ? ». C'est le travail d'un LLM — appelé par API, cadré par un system prompt, contraint à des sorties structurées, et surtout **outillé** : le function calling lui donne accès à TES fonctions (base de recettes, frigo). Ce chapitre pose ces quatre mécanismes avec Azure OpenAI ; le chapitre 18 en fera un agent.

## 1. Azure OpenAI : la plomberie

Côté Azure, tu déploies un modèle dans une ressource : l'**endpoint** (`https://ton-instance.openai.azure.com`), une **clé**, un nom de **déploiement** (ton alias du modèle, ex. `gpt-4o`) et une **api_version**. Les quatre vivent dans la config du chapitre 14 (`settings.azure_openai`), jamais dans le code.

```bash
pip install openai
```

```python
from openai import AzureOpenAI

from config import get_settings

cfg = get_settings().azure_openai
client = AzureOpenAI(
    azure_endpoint=str(cfg.endpoint),
    api_key=cfg.api_key.get_secret_value(),
    api_version=cfg.api_version,
)
```

## 2. Chat completions : messages et paramètres

L'API est une **conversation** : une liste de messages typés par rôle, le modèle produit le message suivant.

```python
reponse = client.chat.completions.create(
    model=cfg.deployment,                    # le nom du DÉPLOIEMENT Azure
    messages=[
        {"role": "system", "content":
         "Tu es un assistant culinaire concis. Tu réponds en français, "
         "en 3 phrases maximum, sans emphase."},
        {"role": "user", "content": "Une idée de dîner avec des oeufs ?"},
    ],
    temperature=0.2,
    max_tokens=300,
)
texte = reponse.choices[0].message.content
```

- **`system`** : le cadrage — ton, format, contraintes, persona. C'est TON levier principal : la différence entre un assistant vague et un composant fiable se joue là.
- **`user`** / **`assistant`** : la conversation. L'API est **sans état** : pour un dialogue suivi, tu renvoies TOUT l'historique à chaque appel (d'où la gestion de contexte, §5).
- **`temperature`** : 0 ≈ déterministe (extraction, classification, code) ; ~0.7-1 pour la créativité (suggestions de menus). Pour tout ce qui alimente du code : **basse**.
- `max_tokens` : borne la réponse (et le coût).

## 3. Sorties structurées : du texte au JSON fiable

Un LLM répond du texte ; ton code veut des données. Demander « réponds en JSON » dans le prompt fonctionne... 95 % du temps — insuffisant. Le **structured output** contraint la génération à un schéma, et Pydantic (chapitre 14) valide à l'arrivée :

```python
from pydantic import BaseModel


class IngredientExtrait(BaseModel):
    nom: str
    quantite: float | None = None
    unite: str | None = None


class RecetteExtraite(BaseModel):
    nom: str
    temps_min: int
    difficulte: int          # 1-3
    ingredients: list[IngredientExtrait]


completion = client.beta.chat.completions.parse(      # .parse : le SDK gère tout
    model=cfg.deployment,
    messages=[
        {"role": "system", "content": "Extrais la recette du texte fourni."},
        {"role": "user", "content": texte_libre},
    ],
    response_format=RecetteExtraite,
)
recette = completion.choices[0].message.parsed        # instance Pydantic validée
```

Le SDK convertit ton modèle Pydantic en JSON Schema, le modèle génère en respectant le schéma, et `parsed` te rend un objet **typé et validé**. À partir de là, le LLM est un composant comme un autre : entrée str, sortie dataclass — testable, branchable sur ta base.

Deux réflexes : garder des schémas **plats et documentés** (descriptions de champs = instructions pour le modèle), et traiter le cas `refusal` (le modèle peut décliner : `message.refusal`).

## 4. Function calling : le modèle appelle TES fonctions

Le mécanisme central du chapitre (et du suivant). Tu **déclares** des outils (nom, description, paramètres en JSON Schema) ; le modèle, au lieu de répondre, peut demander leur exécution ; **ton code** les exécute et renvoie les résultats ; le modèle formule alors sa réponse.

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "chercher_recettes",
        "description": "Cherche les recettes contenant un ingrédient donné.",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient": {"type": "string",
                               "description": "Un ingrédient, ex. 'oeufs'"},
            },
            "required": ["ingredient"],
        },
    },
}]
```

La **boucle** complète — à connaître par cœur :

```python
import json

messages = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Que cuisiner avec des oeufs ?"}]

while True:
    reponse = client.chat.completions.create(
        model=cfg.deployment, messages=messages,
        tools=TOOLS, temperature=0.2,
    )
    msg = reponse.choices[0].message

    if not msg.tool_calls:                     # plus d'outil demandé :
        break                                  # c'est la réponse finale

    messages.append(msg)                       # l'intention d'appel, dans l'historique
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        resultat = executer(call.function.name, args)     # TON code, TES fonctions
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,           # OBLIGATOIRE : relie résultat ↔ appel
            "content": json.dumps(resultat, ensure_ascii=False),
        })

print(msg.content)
```

Points de rigueur :

- `call.function.arguments` est une **chaîne JSON générée par le modèle** : `json.loads` peut échouer, les arguments peuvent être farfelus → valide-les (Pydantic encore) avant d'exécuter. Le modèle PROPOSE, ton code DISPOSE.
- Un tour peut contenir **plusieurs** tool_calls (réponds à chacun, avec le bon `tool_call_id`).
- La qualité des **descriptions** d'outils fait la qualité des appels : décris quand utiliser l'outil, le format exact des paramètres, ce qu'il retourne.
- Borne la boucle (`for _ in range(8)` plutôt que `while True`) : un modèle qui tourne en rond ne doit pas consommer ton budget à l'infini — c'est le premier garde-fou du chapitre 18.

## 5. Contexte, tokens, coûts

Tout se paie en **tokens** (~4 caractères ; comptage précis : `tiktoken`), en entrée ET en sortie — et l'entrée contient tout l'historique à chaque tour. Une boucle d'outils de 6 tours renvoie 6 fois un historique qui grossit : les coûts sont **quadratiques** dans la longueur de conversation.

Conséquences pratiques : des résultats d'outils **compacts** (renvoie 5 recettes pertinentes, pas la base entière) ; tronquer ou résumer l'historique au-delà d'un seuil ; logger `reponse.usage` (prompt_tokens, completion_tokens) dès le premier jour pour savoir ce que chaque fonctionnalité coûte ; et un plafond de dépense par requête utilisateur (max_tokens × tours max).

## 6. Robustesse

Les erreurs de l'API sont celles du chapitre 9, avec leurs réponses habituelles :

| Erreur | Réaction |
|---|---|
| `RateLimitError` (429) | backoff + retry (le SDK en fait déjà un peu) |
| `APITimeoutError`, 5xx | retry borné |
| Contenu filtré (Azure content filter) | pas un bug : gérer le refus proprement |
| JSON d'arguments invalide | re-demander ou échouer proprement — jamais `eval` |

Et le rappel sécurité (chapitres 14/19) : la clé Azure ne quitte jamais le serveur ; les entrées utilisateur qui partent dans les prompts sont des **données non fiables** (l'injection de prompt existe : un texte de recette qui contient « ignore tes instructions » ne doit pas pouvoir piloter tes outils — d'où la validation des arguments côté code).

## Checklist de fin de chapitre

- [ ] Je configure le client AzureOpenAI depuis `get_settings()` (endpoint, clé, déploiement, api_version).
- [ ] Je cadre le comportement par le system prompt et je choisis la temperature selon l'usage.
- [ ] J'obtiens des sorties **typées** avec `.parse` + Pydantic, refus géré.
- [ ] J'écris la boucle de function calling complète (tool_calls, rôle `tool`, tool_call_id) — bornée.
- [ ] Je valide les arguments générés par le modèle avant toute exécution.
- [ ] Je logge l'usage en tokens et je garde les résultats d'outils compacts.
