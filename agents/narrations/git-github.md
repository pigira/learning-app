# Bible narrative — Altitude Sports

## Statut et fonction

Cours : `git-github`, intitulé exact
**Altitude Sports — Git et GitHub, de débutant à avancé**.
Cette bible est un contexte éditorial pour l'architecte et le rédacteur,
pas un document pédagogique lu par le moteur.
Elle ne contient ni code, ni exercice, ni solution, ni projet guidé.
Les métadonnées des 37 chapitres fixent le contrat technique ; la fiction
ne permet pas d'ajouter une compétence, une dépendance ou un livrable inédit.
Le squelette attend la validation de Pierre avant toute rédaction.

## Public et environnement

- Débutant réel : aucune compétence Python, C/C++, shell, algorithmique,
  Git ou GitHub n'est présumée. Le niveau du cours Python ne se transpose
  pas à ce cours ; ses métadonnées sont seulement un patron de forme.
- Windows, macOS et Linux, Git en terminal et VS Code. L'installation
  appartient au parcours des futurs apprenants, pas à l'architecte.
  Les commandes de shell doivent être distinguées des commandes Git.
- Le parcours principal utilise Git Bash sous Windows et les shells
  disponibles sous macOS/Linux ; donner les équivalents PowerShell utiles
  à la navigation, sans imposer WSL. Pour les futurs petits contrôles,
  enseigner et choisir explicitement bash.
- Les chapitres 0 et 1 enseignent l'environnement et le terminal ;
  Markdown arrive au chapitre 14, le YAML et le shell de validation au 26,
  le HTML minimal au 31 uniquement pour la variante de site statique,
  JSON et HTTP au 32. Ne supposer aucun de ces acquis avant son introduction.
- Aucun matériel électronique, achat ou formation Python préalable.
  Connexion et compte autorisé sont nécessaires aux fonctions GitHub
  réelles ; une simulation locale doit être nommée comme telle.
- Une offre GitHub gratuite suffit au parcours principal. LFS, Pages,
  protections, signatures, matrices étendues et outils facultatifs
  doivent avoir un choix motivé ou un repli. Vérifier documentation,
  droits, quotas et éventuels coûts au moment de la rédaction :
  ne pas inventer de disponibilité ni de prix durable.
- L'apprenant peut travailler seul, en alternant les points de vue et
  avec plusieurs copies de démonstration ; ne pas exiger plusieurs
  comptes GitHub ni prétendre qu'une auto-relecture est une approbation tierce.

## Entreprise et continuité

**Altitude Sports** est une entreprise entièrement fictive d'équipements
et de services sportifs. Son équipe prépare une saison autour d'un
catalogue documentaire, d'informations sur des services et d'un guide
de contribution. Le rattachement applicatif reste exclusivement
`Enduro`, jamais « sport », « entreprise » ou le nom de l'entreprise.

L'apprenant rejoint l'équipe, découvre ses documents, les rend traçables,
organise leur collaboration, puis prépare une diffusion et une transmission
fiables. La valeur d'une fonction Git doit venir d'un besoin concret :
retrouver une modification, isoler une variante, relire une proposition,
annuler un changement publié ou retrouver une version.

Les supports restent des fichiers texte, documents Markdown et petits
médias synthétiques quand ils sont utiles. Le cours ne devient ni une
application de commerce ni une formation à la conception de matériel.
Les prestations sportives sont du contexte documentaire, pas des conseils
de santé ou de sécurité à appliquer dans le monde réel.

## Profils fictifs

| Personnage | Rôle dans le fil rouge | Fonction pédagogique |
|---|---|---|
| Alex | Nouvelle recrue documentaire, point de vue de l'apprenant | Pose les questions élémentaires sans connaissance technique présumée. |
| Léa | Coordinatrice du catalogue et des services | Rend explicites les besoins, les critères d'acceptation et les priorités. |
| Samir | Référent documentation et relecture | Compare les versions et explique les décisions sans décider à la place de l'apprenant. |
| Noa | Référente qualité, accès et continuité | Rend les contrôles et les limites de sécurité visibles dès leur première nécessité. |
| Camille | Interlocutrice d'un partenaire fictif | Introduit la contribution externe et les droits restreints, sans être un adversaire caricatural. |

Les personnages ne possèdent pas de comptes réels à contacter.
Leur rôle est simulable par une seule personne. Aucun changement d'équipe
ou nouveau personnage n'est nécessaire pour passer aux sujets avancés.

## Règles de narration et de rédaction

1. Titres JSON : conserver « Altitude : … » suivi d'un sous-titre technique
   précis après le tiret long. Description JSON : une phrase narrative,
   puis une phrase technique. Pour le cours, conserver son titre exact.
2. `objectifs` et `points_theorie` demeurent techniques, observables et
   indépendants des personnages ; aucun champ JSON de narration.
3. Dans la rédaction future, une ouverture brève donne l'utilité métier ;
   le récit ne masque ni prérequis, ni explication, ni limite. Les conflits
   sont des désaccords de contenu à comprendre, jamais des fautes morales.
4. Les lieux des titres sont des repères de l'équipe, pas des énigmes
   bloquantes. Pas d'objet caché, de connaissance sportive spécialisée
   ou de chapitre annexe nécessaire pour comprendre une consigne.
5. Données entièrement synthétiques : aucune identité client, information
   de santé, trace GPS réelle, clé, mot de passe utilisable ou contenu
   d'entreprise. Les alertes n'emploient que des marqueurs inertes.
6. Toute future manipulation qui risque une perte se fait dans un dépôt
   d'essai séparé et recréable, avec sauvegarde et état initial identifiés.
   Le récit ne justifie jamais une suppression précipitée ou une commande
   exécutée sur le dépôt de l'application de learning.
7. Pas de réécriture d'historique partagé sans concertation explicite,
   ni de forçage présenté comme solution aux divergences. L'annulation
   d'un changement publié conserve normalement une trace.
8. Un fork ou un résultat de workflow n'est pas fiable par défaut.
   Validation sans secret et privilèges minimaux dès le premier workflow ;
   aucun code externe exécuté dans un contexte privilégié.
9. Les variantes avancées sont comparées puis retenues seulement si utiles.
   Refuser un submodule ou un cache inutile démontre une compétence,
   ce n'est pas une lacune à compenser artificiellement.
10. Les séances indépendantes de rédaction lisent les théories antérieures
    disponibles : le squelette fige la progression, mais ne prouve pas qu'une
    notion est enseignée. Introduire localement les prérequis absents dans
    une mesure raisonnable, sinon signaler un blocage ; ne modifier que le
    chapitre demandé et sa ligne README, relue juste avant édition.

## Arc par chapitre

### 0 à 6 — Passer des dossiers manuels à un historique fiable

| # | Repère narratif | Transition technique |
|---|---|---|
| 0 | Alex rejoint l'équipe. | Installer et orienter, sans connaissance préalable. |
| 1 | Le casier de travail est organisé. | Naviguer et lire les commandes sans danger. |
| 2 | Un registre remplace les copies de versions. | Créer le dépôt et nommer ses trois états. |
| 3 | Les premières fiches sont consignées. | Construire et vérifier les commits. |
| 4 | Une relecture demande ce qui a changé. | Inspecter l'historique et les différences. |
| 5 | Les documents partageables sont séparés des exports locaux. | Définir suivi, exclusions et confidentialité. |
| 6 | Une correction locale doit être reprise. | Restaurer une cible précise sans perdre les brouillons. |

### 7 à 16 — Apprendre à décider et travailler ensemble

| # | Repère narratif | Transition technique |
|---|---|---|
| 7 | Une variante du catalogue est envisagée. | Isoler le travail avec une branche. |
| 8 | Les variantes doivent rejoindre la référence. | Comprendre les formes de fusion. |
| 9 | Deux modifications portent sur la même fiche. | Résoudre le conflit de sens et de texte. |
| 10 | Un point de rencontre distant est ouvert. | Protéger le compte et choisir l'authentification. |
| 11 | Les documents rejoignent GitHub. | Relier les dépôts et publier une branche. |
| 12 | Deux postes font évoluer la même référence. | Observer puis intégrer les changements distants. |
| 13 | Samir organise une relecture. | Préparer et traiter une pull request. |
| 14 | Léa rend le planning visible. | Articuler documentation, issues et tableau. |
| 15 | Camille propose une contribution externe. | Utiliser un fork et respecter ses droits. |
| 16 | L'équipe choisit ses règles communes. | Motiver le workflow et la gouvernance. |

### 17 à 25 — Maîtriser les situations qui sortent du chemin simple

| # | Repère narratif | Transition technique |
|---|---|---|
| 17 | Une urgence interrompt un brouillon. | Choisir stash, commit ou worktree. |
| 18 | Une série privée est rendue lisible. | Réécrire localement sans réécrire le travail partagé. |
| 19 | Un correctif ciblé doit être reporté. | Choisir cherry-pick ou revert traçable. |
| 20 | Une branche semble avoir disparu. | Retrouver un commit et comprendre les limites de récupération. |
| 21 | Une incohérence ancienne est signalée. | Enquêter sans accuser avec blame et bisect. |
| 22 | L'équipe veut comprendre les mécanismes. | Relier objets, références et accessibilité. |
| 23 | Les trois systèmes doivent rester compatibles. | Maîtriser attributs, fins de ligne et noms. |
| 24 | Les médias fictifs prennent plus de place. | Choisir stockage et périmètre des clones. |
| 25 | Un kit documentaire est partagé. | Évaluer puis épingler une dépendance Git. |

### 26 à 35 — Contrôler, diffuser et transmettre

| # | Repère narratif | Transition technique |
|---|---|---|
| 26 | Noa explicite une fiche de contrôle. | Apprendre le YAML et le shell strictement nécessaires. |
| 27 | La fiche accompagne chaque proposition. | Introduire une CI minimale et sûre. |
| 28 | Les résultats doivent être comparables et retrouvables. | Borner matrices, artefacts et caches. |
| 29 | L'ouverture aux partenaires doit rester contrôlée. | Séparer contenu non fiable et privilèges. |
| 30 | Une sortie de saison est identifiée. | Associer version, tag et release. |
| 31 | Une vitrine documentaire est préparée. | Organiser les pages et choisir la publication. |
| 32 | L'équipe consulte son état d'avancement. | Lire GitHub par CLI et API. |
| 33 | Les responsabilités d'accès évoluent. | Distinguer habilitation, identité et signature. |
| 34 | Une alerte fictive teste l'organisation. | Prévenir, confiner et signaler sans divulgation. |
| 35 | La transmission de la saison est préparée. | Vérifier sauvegarde, maintenance et migration. |

### 36 — Une saison complète, sans compétence nouvelle

L'équipe relie les étapes déjà apprises, de la demande initiale à une
version documentée, relue et récupérable. Le chapitre final réemploie les
acquis techniques et les décisions de méthode ; il n'introduit ni nouvel
outil obligatoire, ni service payant, ni application à programmer.
Les options avancées peuvent être motivées puis écartées ou démontrées
séparément dans un espace isolé. Le résultat attendu reste compréhensible
par une personne qui a suivi les chapitres précédents, sans solution cachée
dans la narration.
