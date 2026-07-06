Vingt-et-un chapitres de briques. Ce dernier chapitre ne t'apprend pas une technologie de plus : il t'apprend à **assembler** — cadrer un MVP, l'architecturer, le livrer présentable. C'est la compétence qui sépare « je connais Python » de « je mène un projet de bout en bout », celle que visait tout le parcours. On l'applique au projet Cuisine (le plus complet), mais la méthode vaut pour les trois.

## 1. Cadrer un MVP

Un **MVP** (Minimum Viable Product) est la plus petite version qui rend un service réel. La difficulté n'est pas d'ajouter — c'est de **retrancher**. Sans discipline de périmètre, un projet perso s'étale sur six mois et ne sort jamais.

La méthode : lister les **user stories** (« En tant qu'utilisateur, je veux X pour Y »), puis les trier sans pitié.

```
DANS le MVP Cuisine :
  - importer/consulter des recettes (base + API TheMealDB)
  - déclarer mon frigo et mes contraintes (allergies, régime)
  - demander un plan de repas en langage naturel (agent IA)
  - obtenir la liste de courses

HORS MVP (versions futures) :
  - comptes multi-utilisateurs
  - photos des plats, notation
  - app mobile
  - suggestions selon la saison / le budget optimisé
```

Écrire explicitement ce qu'on REFUSE de faire est aussi important que la liste des fonctionnalités — c'est la digue contre le *scope creep*. Un MVP se définit par ses limites autant que par son contenu.

## 2. Architecturer en couches

L'assemblage réussit quand les responsabilités sont séparées — le fil rouge de tout le parcours. Les quatre couches :

```
┌─ Présentation ──── Streamlit / FastAPI+templates (ch. 12, 13)
├─ IA ───────────── agent + LLM (ch. 17, 18)
├─ Métier ───────── recherche, planification, règles, contraintes (ch. 2, 4, 18)
├─ Données ──────── SQLite, API externes, fichiers (ch. 5, 6, 9, 16)
└─ Transverse ───── config (14), tests (7), sécurité (19)
```

Règle de dépendance, apprise dès le chapitre 4 : les flèches pointent vers le BAS. La présentation dépend du métier, le métier des données — jamais l'inverse. Le métier ne sait pas s'il est affiché en Streamlit ou en CLI ; les données ne savent pas qu'un agent les consomme. Cette discipline rend chaque couche testable et remplaçable isolément.

Le flux type du MVP Cuisine :

```
API TheMealDB / saisie ─→ SQLite (recettes, frigo, profil)
                              │
                       moteur métier (recherche, réalisables, courses)
                              │
                       agent planificateur ←── contraintes vérifiées par le code
                              │
                       Streamlit (plan de la semaine, liste de courses)
```

## 3. Documenter les décisions

Un projet qu'on reprend dans trois mois (ou qu'un recruteur lit) a besoin de savoir POURQUOI, pas seulement QUOI. Le mini-**ADR** (Architecture Decision Record) est un paragraphe par décision structurante :

```markdown
## ADR-003 : SQLite plutôt que PostgreSQL
Contexte : app perso, mono-utilisateur, données modestes.
Décision : SQLite (fichier unique, zéro serveur, inclus dans Python).
Conséquences : + simplicité, déploiement trivial ; − pas de concurrence
d'écriture forte (acceptable ici). Migration Postgres possible plus tard
(SQLAlchemy limiterait le coût).
```

Trois à cinq ADR suffisent pour un MVP : le choix de la base, de l'interface, de l'approche IA, de la structure. Ils transforment des choix implicites en décisions assumées — et montrent une maturité d'ingénieur bien plus qu'un README de features.

## 4. La qualité de livraison

« Ça tourne chez moi » n'est pas fini. Un MVP livrable réunit :

- **Les tests des chemins critiques** (chapitre 7) : pas 100 % de couverture, mais les 5-6 scénarios dont l'échec serait grave — une allergie jamais violée (chapitre 18), un upsert sans doublon, un secret jamais exposé (chapitre 19). Ceux-là sont verts, toujours.
- **Un README qui permet de démarrer en 5 minutes** : ce que fait l'app, installation, lancement (`docker compose up`, chapitre 20), une capture ou deux. Le premier contact — soigne-le.
- **Une démo reproductible** : un jeu de données d'exemple et un scénario scripté (« lance ça, tu verras un plan de semaine »). Une démo qui échoue devant un recruteur vaut moins que pas de démo.
- **Un déploiement propre** : dockerisé (chapitre 20), config externalisée (chapitre 14), secrets hors du dépôt (chapitre 19).

## 5. Construire dans le bon ordre

L'erreur classique est de commencer par le plus excitant (l'agent IA) sur des fondations absentes. L'ordre qui marche va du bas vers le haut, chaque étage posé sur un étage testé :

1. **Squelette + données** : structure du repo, config (14), schéma SQLite (6), quelques données réelles. Rien d'intelligent, mais ça tourne.
2. **Métier** : recherche, réalisables, courses (2, 4) — avec leurs tests. Le cœur fonctionne en CLI, sans IA.
3. **IA** : function calling puis agent (17, 18) branché sur le métier existant. Les contraintes dures vérifiées par le code.
4. **Présentation** : Streamlit ou FastAPI par-dessus (12, 13). Elle ne fait qu'afficher.
5. **Livraison** : tests des chemins critiques, Docker (20), sécurité (19), README.

À chaque étape, quelque chose de DÉMONTRABLE fonctionne. On ne construit jamais deux étages en l'air : si le métier n'est pas testé, l'agent posé dessus amplifiera ses bugs au lieu de les révéler.

## 6. Assumer la dette, prévoir la suite

Un MVP a des raccourcis — c'est légitime, à condition d'être **conscient et documenté**. La rétrospective honnête :

- **Dette assumée** : « pas d'authentification (mono-utilisateur) », « prix des ingrédients codés en dur », « pas de cache Redis (SQLite suffit à cette échelle) ». Chacune est un choix, pas un oubli.
- **Suites possibles** : ce que tu ferais avec plus de temps — multi-utilisateurs, optimisation du budget courses, appli mobile. Montre que tu vois au-delà du MVP.

Cette lucidité — savoir ce qu'on n'a pas fait et pourquoi — est un signe de séniorité plus fort que n'importe quelle fonctionnalité. Un ingénieur qui livre un MVP net avec une dette assumée est plus employable qu'un autre qui promet tout et ne finit rien.

## 7. Ce que ce projet prouve

Au terme du parcours, tu ne « connais pas Python » — tu sais mener un projet logiciel complet : cadrer, architecturer en couches, intégrer une API et une IA, persister, tester, sécuriser, dockeriser, documenter. C'est exactement le profil visé : autonome de bout en bout, capable d'intégrer l'IA dans ses projets, employable au-delà de son poste actuel. Les trois apps cibles (Cuisine, Finance, Enduro) ne sont plus des idées — ce sont des assemblages de briques que tu maîtrises.

## Checklist de fin de chapitre (et de parcours)

- [ ] Je cadre un MVP par des user stories et j'écris explicitement ce qui est HORS périmètre.
- [ ] J'architecture en couches à dépendances descendantes (présentation → métier → données).
- [ ] Je documente mes 3-5 décisions structurantes (ADR).
- [ ] Je construis du bas vers le haut, chaque étage démontrable et testé.
- [ ] Je livre : tests des chemins critiques, README, démo reproductible, Docker, secrets hors dépôt.
- [ ] Je sais nommer ma dette technique assumée et les suites possibles.
