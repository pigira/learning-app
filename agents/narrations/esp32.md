# Le Laboratoire Scellé — Bible du cours `esp32`

## Statut et usage

Note de contexte destinée à `architecte-cours` et `redacteur-chapitre`, hors
contenu chargé par l'application. Le contrat de progression est constitué de
`app/content/esp32/cours.json` et des quinze `chapitre.json`, à valider par
Pierre avant rédaction. Le cours distinct `esp32-microcontroleurs` est conservé.

Cette bible n'est ni une leçon, ni un catalogue d'exercices, ni une solution.
Ne pas la convertir en champs JSON supplémentaires. Dans les métadonnées, la
fiction demeure exclusivement dans `titre` et `description` ; les objectifs
et les points de théorie restent techniques.

## Personnage, ton et règles de l'univers

Pierre se réveille dans un laboratoire abandonné. **Adrien Valen**, ingénieur
fictif disparu avant son arrivée, a laissé des carnets d'observation et des
messages incomplets. Il n'est ni un adversaire ni une autorité infaillible :
ses notes donnent un contexte, jamais une dispense de vérifier un branchement.
L'identité et le sort de l'ingénieur ne sont pas une énigme technique à résoudre.

Le fil conducteur est la reconstruction méthodique de dispositifs en panne.
Chaque salle rend intelligible la suivante : alimentation, entrées, mesures,
signalisation, coordination, communication puis intégration. Les traces
retrouvées donnent une continuité au parcours sans ajouter de connaissances
obligatoires hors du plan. Aucun code secret, mécanisme ou achat caché n'est
nécessaire pour avancer.

Ton : curiosité, calme, exploration et satisfaction d'un résultat vérifiable.
Pas d'urgence menaçante, de punition pour erreur ou d'essai électrique imposé
par la fiction. « Scellé » et « sortie » sont des conventions narratives :
la sortie finale est symbolisée par une indication de maquette, jamais par
une véritable serrure ou un équipement assurant la sécurité d'une personne.

Les quinze salles ne sont pas quinze appareils conservés physiquement :
Pierre dispose d'une seule carte et d'une seule breadboard. Les montages sont
démontés hors tension et les composants réemployés. La continuité appartient
au récit et aux observations, pas à un inventaire matériel multiplié.

## Fil conducteur et contrat des prérequis

| Salle | Continuité narrative | Acquis techniques mobilisés en amont |
|---|---|---|
| 00 — Le réveil | Retrouver une première lumière et une console lisible. | Aucun acquis électronique ; alimentation, breadboard et résistance protectrice introduites localement. |
| 01 — Le signal | Rendre le voyant commandable et compréhensible. | 00 : circuit LED et outils. |
| 02 — Le clavier | Rendre les commandes locales fiables. | 00–01 : console, GPIO, résistance ; `millis()` introduit ici. |
| 03 — La jauge | Interpréter une variation plutôt qu'un simple état. | 01–02 : loi d'Ohm, entrée numérique et échantillonnage minimal. |
| 04 — Les balises | Donner une forme lumineuse ou sonore aux indications. | 01–03 : budget de courant, GPIO, potentiomètre et normalisation. |
| 05 — L'horloge | Faire coexister les tâches sans immobiliser les commandes. | 02 et 04 : anti-rebond, première temporisation et sorties. |
| 06 — Le passage | Recueillir les événements sans manquer leur arrivée. | 02 et 05 : entrées et boucle réactive ; ISR et partage de données introduits ici. |
| 07 — La veille | Comprendre le temps propre d'un détecteur. | 01, 05–06 : GPIO, temporisations, identification d'une sortie. |
| 08 — L'atmosphère | Distinguer relevé exploitable et relevé manquant. | 02, 05, 07 : rappel, cadence, niveaux et alimentation. |
| 09 — Le pupitre | Rendre les informations locales lisibles. | 02, 05, 08 : pull-up, rafraîchissement, validité des données. |
| 10 — La commande | Séparer décision électrique et charge commutée. | 01–02, 05, 07 : courants, bouton, temps et rail USB/VIN. |
| 11 — La logique | Réconcilier les comportements des dispositifs. | 02, 05–06, 08–10 : événements, erreurs, affichage et repos. |
| 12 — La liaison | Retrouver un échange local avec le terminal. | 03–05, 09, 11 : ADC1, PWM, ordonnanceur, OLED et FSM. |
| 13 — Le silence | Suspendre l'activité puis repartir proprement. | 02, 05, 10–12 : bouton, temps, repos, FSM et réseau. |
| 14 — La sortie | Réunir les acquis dans un pupitre cohérent. | 00–13 : intégration sans API ni composant nouveau. |

Ce tableau fixe les dépendances du plan, pas l'existence de théories déjà
rédigées. Chaque session de rédaction lit les métadonnées antérieures et les
théories préalables disponibles. Une théorie manquante impose d'introduire
localement le minimum nécessaire ou de signaler le blocage, jamais de considérer
la notion enseignée parce qu'un squelette l'annonce.

## Public, outils et cadence

- C/C++ et algorithmique solides, aucune pratique récente de l'électronique
  ou des microcontrôleurs. Aucun prérequis Python et aucun cours de langage C++.
  Les références Python du dépôt calibrent la pédagogie, pas les compétences
  ni les bibliothèques à exiger pour ce cours.
- VS Code, extension PlatformIO et framework Arduino C++ exclusivement.
  Proposer des parcours Windows, macOS et Linux, sans supposer l'OS de Pierre.
  Le Python éventuellement géré en interne par PlatformIO n'est pas un sujet
  à apprendre ni un second environnement pédagogique à configurer.
- Base commune figée : `platformio/espressif32@6.9.0`,
  `platformio/framework-arduinoespressif32@3.20017.0`, Arduino-ESP32 **2.0.17**.
  Le manifeste officiel
  [PlatformIO Espressif32 v6.9.0](https://github.com/platformio/platform-espressif32/blob/v6.9.0/platform.json)
  a été consulté pour le squelette ; il déclare `~3.20017.0`.
  La rédaction doit montrer le gel exact et le contrôle des versions résolues,
  sans exécuter elle-même compilation ou téléversement.
- Les API LEDC sont celles de la branche 2.x, notamment la sélection par canal.
  Ne pas y mélanger les appels ou signatures 3.x. Les bibliothèques DHT et OLED
  seront identifiées, vérifiées et figées lors de leur introduction, sans
  dépendance implicite. Une modification du socle commun exige une décision
  coordonnée, pas un changement isolé par un rédacteur.
- Les outils et bibliothèques nécessitent un téléchargement initial ou un cache
  déjà disponible. Leur installation ne signifie pas que les montages ont
  besoin d'Internet : aucune API, compte, abonnement ou service externe à
  l'exécution. Aucun routeur ou smartphone imposé ; point d'accès ESP32 local
  authentifié si aucun réseau 2,4 GHz autorisé n'est disponible. Vérifier que
  l'ordinateur peut établir la liaison Wi-Fi ; ne pas inventer un adaptateur.
- Cible : **1 à 2 heures par chapitre**, avec une réalisation centrale courte.
  Les exemples sectoriels sont des alternatives, pas trois projets complets
  obligatoires à chaque fois. Le diagnostic d'installation ou une identification
  matérielle bloquante peut dépasser cette cible ; ne pas promettre un temps
  certain. L'intégration réemploie les sous-ensembles déjà compris.

## Inventaire exact déclaré

| Quantité | Matériel |
|---|---|
| 1 | Carte ESP32-WROOM32, 30 broches (15 par côté), USB-série CP2102, connecteur micro-USB |
| 1 | OLED SSD1306, 0,96 pouce, 128×64, I2C, quatre broches GND VDD SCK SDA |
| 1 | Breadboard 830 points |
| 1 | Module IR obstacle, référence supplémentaire non fournie |
| 1 | Module photorésistance, sorties AO/DO à identifier |
| 1 | Module DHT11 |
| 1 | PIR HC-SR501 |
| 1 | Potentiomètre 10 kΩ |
| 1 | Câble micro-USB |
| 30 au total | Résistances parmi 220 Ω, 1 kΩ et 10 kΩ ; répartition inconnue, pas dix de chaque par défaut |
| 1 de chaque | Buzzer passif et buzzer actif |
| 1 | Module relais 5 V, deux canaux |
| 6 | Boutons |
| 10 de chaque | Dupont F-M, F-F et M-M |
| 5 de chaque | LED rouges, jaunes et vertes |
| 1 | LED RGB, commun et brochage à identifier |

Aucun multimètre, alimentation de laboratoire, alimentation 5 V externe,
condensateur, transistor ou autre composant discret n'est déclaré. Aucun achat
futur ni accessoire supplémentaire ne peut résoudre implicitement une difficulté.
Avant une réalisation, relever les quantités par valeur et la connectique réelle.
Le budget tient compte des ponts de rails et des connexions d'alimentation,
pas seulement des signaux. Ne jamais dépasser dix fils d'un type.

## Compatibilité déclarée et vérifications indispensables

Pierre a déclaré : « tout ce que j'ai mentionne est compatible c'est un kit
d'apprentissage ». Cette déclaration permet de cadrer le squelette, mais
**n'est pas une vérification documentaire**. L'annonce AliExpress
`1005008528536556` était inaccessible ; aucune spécification technique n'en a
été extraite. Ne pas réclamer une nouvelle fiche pour justifier rétrospectivement
la création du plan, ni inventer une preuve de compatibilité.

À la rédaction puis avant chaque branchement par l'apprenant, identifier la
carte et le module effectivement utilisés : brochage, plage d'alimentation,
niveaux de sortie/entrée, courants, rappels intégrés et états au démarrage.
Une donnée critique inconnue impose de signaler un **blocage**, sans essai sous
tension, achat de contournement ou composant supposé. Une variante avec bouton
ou LED peut enseigner une notion mais ne valide pas un module resté non identifié.

La photo annotée de la carte n'est pas un brochage de référence : D14 est GPIO14,
pas GPIO36 ; GPIO26 correspond à DAC2 ; plusieurs annotations ADC/touch sont
erronées. Utiliser sérigraphie et documentation ESP32 classique, jamais les
numéros de positions physiques recopiés de l'image. La largeur réelle peut
imposer de laisser la carte hors breadboard avec les Dupont disponibles.

## Limites électriques et d'usage communes à la rédaction

- Logique **3,3 V**, GPIO non tolérants à 5 V. Éviter GPIO0/2/5/12/15
  de strapping, GPIO6–11 de flash ; réserver UART0 à la console.
  GPIO34–39 : entrées seules, sans pulls internes, pas tous exposés.
  Choisir ADC1 pour conserver la mesure analogique avec Wi-Fi.
- Source unique USB. Aucun branchement d'alimentation externe, retour
  d'alimentation ou tension improvisée. PIR et relais en 5 V uniquement
  si le rail USB/VIN de la carte exacte est documenté comme sortie utilisable
  et si son budget le permet. Une plage générique « 5–12 V » n'est pas
  une autorisation d'alimentation.
- Référence de masse adaptée au circuit réel : masse commune pour une commande
  non isolée ; ne pas supposer qu'un relais avec optocoupleur éventuel offre
  automatiquement une isolation galvanique. Séparer alimentation, commande
  et contacts dans l'explication.
- LED avec résistance série calculée ; RGB avec **une résistance par couleur**.
  Budget de courant conservateur et limites cumulées, jamais maxima absolus
  présentés comme cible. Ne commander aucune bobine brute.
- Relais et buzzers : aucune promesse de commande GPIO directe sans entrée,
  tension et courant compatibles documentés. Le second canal du relais ne
  doit pas flotter vers une activation indésirable. Son état de repos et
  celui du canal utilisé doivent être examinés avant `setup()` également.
- Relais : charge du socle limitée à une LED avec résistance en basse tension.
  Un buzzer ne serait admissible qu'après justification de ses caractéristiques.
  **Aucun 230 V ni autre tension secteur**, serrure réelle, chauffage, appareil,
  véhicule ou dispositif destiné à la sécurité.
- Tout câblage ou démontage se fait USB débranché. Le contrôle visuel hors
  tension sans multimètre ne prouve pas les tensions, les courants ou
  l'absence de tous les défauts.
- Le filtre RC est expliqué **en théorie seulement** : aucun condensateur
  dans le kit. Le montage du chapitre 02 utilise boutons et rappels avec
  anti-rebond logiciel ; une résistance de rappel seule n'est pas un
  anti-rebond matériel.
- Un module photorésistance n'a pas nécessairement AO. DO indique un seuil,
  pas une mesure analogique de lumière ; le potentiomètre garantit la
  pratique ADC sans dépendre de cette identification.
- DHT11 : protocole propre, pas Dallas OneWire ; lecture espacée, erreurs et
  vieillissement des valeurs explicites. Usage Cuisine d'observation,
  sans certification de conservation ou de sécurité alimentaire.
- OLED confirmé I2C : son SCK désigne SCL, pas un bus SPI. Vérifier alimentation
  et tension des pull-up du module avant d'utiliser les lignes de données.
- ISR courtes : aucune console, attente, activité Wi-Fi ou I2C. `volatile`
  ne suffit pas à protéger les échanges composés avec la boucle principale.
- Wi-Fi authentifié et local, HTTP sans données réelles ; aucune exposition
  Internet, secret réel ou commande distante du relais, même indirecte.
  Statut, donnée fictive et LED suffisent.
- Deep sleep : ne pas confondre consommation de la puce et de la carte USB
  avec CP2102, régulateur et voyants. Aucun résultat en µA mesuré ni économie
  certifiée sans instrument. Le sommeil ne coupe pas automatiquement
  l'alimentation des modules.

## Usages personnels et intégration

`Tous` signifie varier les exemples entre Cuisine, Finance et Enduro, sans
créer de secteur « électronique ». Cuisine : minuterie et buzzer seulement
si admissible, suivi température/humidité sur OLED sans fonction sanitaire.
Enduro : intervalles et comptages IR/bouton **sur table**, jamais sur véhicule.
Finance : données fictives reçues du navigateur en Wi-Fi local, affichage
OLED et seuil lumineux/RGB, sans données bancaires, API ni conseil financier.
Avant le chapitre 12, une donnée Finance est explicitement définie localement.

Le final vise une base DHT11 + IR, OLED, un canal relais et LED résistive :
plusieurs entrées, un écran, une commande locale. Avant de la présenter comme
réalisable, le rédacteur doit établir une nomenclature **sur les connecteurs
réels**, la table GPIO et le bilan de courants et de chaque liaison F-M/F-F/M-M.
Ne pas annoncer un nombre de fils fictivement « vérifié » sans ce relevé.
Les conditions d'alimentation et de commande du relais restent des points
bloquants explicites ; une base privée de relais n'est pas le final complet.

PIR, potentiomètre/photorésistance, boutons, RGB, buzzers et sommeil sont des
variantes **successives** avec réemploi et nouveau contrôle des budgets.
Elles mobilisent l'ensemble des acquis sans prétendre que tout tient
simultanément dans les fils, les GPIO ou le courant disponibles.

## Discipline de livraison

L'architecte ne rédige que les métadonnées, cette bible et la section README
du cours. Aucun programme matériel n'est exécuté ni téléversé par les agents.
Après validation du plan par Pierre, chaque invocation indépendante de
`redacteur-chapitre` est limitée à son chapitre et à sa ligne README, relue
juste avant édition pour préserver les mises à jour concurrentes. Les autres
chapitres, la bible, `cours.json`, le moteur et la progression restent intacts.
L'ouverture du cours est une décision ultérieure coordonnée, pas un effet
secondaire d'une session parallèle.
