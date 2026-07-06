Ce chapitre met en place tout ce dont les 21 suivants ont besoin : un terminal maîtrisé, Python proprement installé, des environnements virtuels systématiques et VS Code configuré. Tout est spécifique macOS.

## 1. Le terminal macOS

Ouvre **Terminal** : `Cmd + Espace` (Spotlight) → tape « Terminal » → Entrée. Le shell par défaut de macOS est **zsh**. Le prompt ressemble à :

```
pierre@MacBook-Pro ~ %
```

`~` est ton dossier personnel (`/Users/pierre`). Tout ce que tu tapes est une commande, éventuellement suivie d'options (`-l`) et d'arguments (`Documents`).

### Commandes essentielles

| Commande | Rôle | Exemple |
|---|---|---|
| `pwd` | Afficher le dossier courant | `pwd` |
| `ls` | Lister le contenu | `ls -l` (détail), `ls -a` (fichiers cachés), `ls -lh` (tailles lisibles) |
| `cd` | Changer de dossier | `cd Documents`, `cd ..` (parent), `cd ~` (home), `cd -` (précédent) |
| `mkdir` | Créer un dossier | `mkdir projet`, `mkdir -p a/b/c` (niveaux intermédiaires) |
| `touch` | Créer un fichier vide | `touch main.py` |
| `cp` | Copier | `cp a.txt b.txt`, `cp -R dossier/ copie/` |
| `mv` | Déplacer **ou renommer** | `mv brouillon.txt notes.txt` |
| `rm` | Supprimer (définitif, pas de corbeille) | `rm fichier.txt`, `rm -r dossier/` |
| `cat` / `less` | Afficher un fichier (`less` : paginer, `q` pour quitter) | `cat notes.txt` |
| `open` | Ouvrir avec l'app macOS associée | `open .` (Finder ici), `open rapport.pdf` |
| `which` | Localiser un exécutable | `which python3` |
| `history` | Historique des commandes | `history` |
| `clear` | Nettoyer l'écran | `clear` (ou `Cmd + K`) |

### Chemins

- **Absolu** : part de la racine — `/Users/pierre/Documents/projet`
- **Relatif** : part du dossier courant — `Documents/projet`, `../autre`
- `~` est développé en ton home : `~/Documents` ≡ `/Users/pierre/Documents`
- Un chemin contenant des espaces doit être quoté : `cd "Mon Dossier"` (ou échappé : `Mon\ Dossier`)

### Réflexes de productivité

- **Tab** : autocomplétion des noms de fichiers/commandes — à utiliser en permanence.
- **Flèche haut/bas** : naviguer dans l'historique.
- **Ctrl + R** : recherche dans l'historique (tape quelques lettres, Entrée).
- **Ctrl + C** : interrompre la commande en cours.
- Glisser un dossier depuis le Finder dans le Terminal colle son chemin absolu.

## 2. Permissions

`ls -l` affiche une chaîne de permissions par fichier :

```
-rwxr-xr--  1 pierre  staff  512 6 jul 10:00 script.sh
```

Décodage de `-rwxr-xr--` : le premier caractère est le type (`-` fichier, `d` dossier), puis trois triplets `rwx` (read/write/execute) pour **le propriétaire**, **le groupe**, **les autres**. Ici : le propriétaire peut tout faire, le groupe peut lire et exécuter, les autres seulement lire.

Modifier les permissions avec `chmod` :

```bash
chmod +x script.sh    # rend exécutable (cas le plus courant)
chmod 755 script.sh   # notation octale : r=4, w=2, x=1 → 755 = rwxr-xr-x
```

`sudo` exécute une commande avec les droits administrateur. Règle : si tu as besoin de `sudo` pour travailler dans ton propre projet, c'est que quelque chose est mal installé — n'en fais jamais un réflexe (en particulier, jamais `sudo pip`).

## 3. Homebrew

[Homebrew](https://brew.sh) est le gestionnaire de paquets standard sur macOS : il installe et met à jour les outils de développement. Installation (commande officielle, à copier depuis brew.sh) :

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Usage courant :

```bash
brew install wget        # installer un outil
brew list                # ce qui est installé
brew update && brew upgrade   # mettre à jour Homebrew puis les paquets
```

## 4. Python sur macOS

macOS embarque un Python système : **ne l'utilise jamais pour développer** (version figée, utilisé par l'OS). Installe le tien :

```bash
brew install python@3.12
python3 --version    # Python 3.12.x
which python3        # /opt/homebrew/bin/python3 (Apple Silicon)
```

Trois façons d'exécuter du Python :

```bash
python3                  # REPL interactif : tester une expression, exit() pour sortir
python3 script.py        # exécuter un fichier
python3 -c "print(2**10)"   # une ligne à la volée
```

Un script peut aussi devenir directement exécutable avec une ligne **shebang** en tête de fichier :

```python
#!/usr/bin/env python3
print("bonjour")
```

```bash
chmod +x script.py
./script.py
```

## 5. Environnements virtuels et pip

**Le problème** : deux projets peuvent exiger des versions incompatibles d'une même librairie. Installer globalement = conflits garantis.

**La solution** : un environnement virtuel (**venv**) par projet — une copie isolée de Python avec ses propres packages, dans un dossier `.venv` à la racine du projet.

```bash
cd mon_projet
python3 -m venv .venv          # création (une seule fois)
source .venv/bin/activate      # activation : le prompt affiche (.venv)
which python3                  # → mon_projet/.venv/bin/python3 : c'est bon
```

Une fois activé, `pip` installe **dans le venv** :

```bash
pip install requests           # installer
pip list                       # packages présents
pip show requests              # détail d'un package
pip freeze > requirements.txt  # geler les versions exactes dans un fichier
pip install -r requirements.txt   # réinstaller à l'identique (autre machine, collègue)
deactivate                     # sortir du venv
```

Règles d'or :

- Un venv **par projet**, toujours nommé `.venv` (convention reconnue par VS Code).
- Jamais de `pip install` hors venv.
- `.venv/` ne se versionne pas (il va dans `.gitignore`) ; c'est `requirements.txt` qui fait foi.

## 6. VS Code

Installation :

```bash
brew install --cask visual-studio-code
```

Puis installe la commande `code` dans le PATH : ouvre VS Code, `Cmd + Shift + P` → « Shell Command: Install 'code' command in PATH ». Ensuite, depuis le terminal, `code .` ouvre le dossier courant comme projet.

### L'interface, en cinq zones

- **Explorateur** (barre latérale gauche) : les fichiers du dossier ouvert. VS Code travaille par *dossier-projet*, pas par fichier isolé — ouvre toujours la racine du projet.
- **Éditeur** (centre) : onglets de fichiers.
- **Terminal intégré** (bas, `Ctrl + ù` sur clavier FR / `` Ctrl + ` `` sinon) : un vrai zsh dans le dossier du projet. C'est ici que tu actives le venv et lances tes scripts.
- **Palette de commandes** (`Cmd + Shift + P`) : accès à toutes les actions par leur nom. Le réflexe le plus important de VS Code.
- **Barre d'état** (bas) : affiche notamment l'interpréteur Python actif — surveille-la.

### Extensions indispensables

Onglet Extensions (`Cmd + Shift + X`) :

- **Python** (Microsoft) — exécution, débogage, sélection d'interpréteur.
- **Pylance** (installé avec la précédente) — autocomplétion, vérification de types, navigation dans le code.

### Lier VS Code au venv

`Cmd + Shift + P` → « Python: Select Interpreter » → choisis `./.venv/bin/python`. VS Code propose en général le `.venv` automatiquement dès qu'il existe. À partir de là, le terminal intégré active le venv tout seul et Pylance résout tes imports.

### Le débogueur

Le débogueur remplace les `print()` de diagnostic : il montre l'état réel du programme, ligne par ligne.

1. Clique dans la marge à gauche d'un numéro de ligne (ou `F9`) : un point rouge = **breakpoint**.
2. `F5` (ou panneau « Run and Debug » → « Python File ») : l'exécution démarre et **s'arrête** au breakpoint.
3. Panneau de gauche : **Variables** (état local), **Watch** (expressions à surveiller), **Call Stack** (pile d'appels).
4. Barre de contrôle : **Continue** (`F5`), **Step Over** (`F10`, ligne suivante), **Step Into** (`F11`, entrer dans la fonction appelée), **Step Out** (`Shift + F11`), **Stop** (`Shift + F5`).

### Raccourcis à mémoriser

| Raccourci | Action |
|---|---|
| `Cmd + P` | Ouvrir un fichier par son nom |
| `Cmd + Shift + P` | Palette de commandes |
| `Ctrl + ù` | Terminal intégré (clavier FR) |
| `Cmd + B` | Afficher/masquer la barre latérale |
| `Cmd + /` | Commenter/décommenter la sélection |
| `Option + ↑/↓` | Déplacer la ligne courante |
| `Shift + Option + ↓` | Dupliquer la ligne |
| `Cmd + D` | Sélectionner l'occurrence suivante du mot (multi-curseur) |
| `F2` | Renommer un symbole partout |
| `Cmd + Shift + F` | Rechercher dans tout le projet |

## 7. Structure de projet et PEP 8

### Arborescence type d'un projet Python

```
mon_projet/
├── .venv/               # environnement virtuel (jamais versionné)
├── .gitignore           # .venv/, __pycache__/, *.pyc, .DS_Store
├── README.md            # quoi, comment installer, comment lancer
├── requirements.txt     # dépendances gelées
├── src/                 # le code (ou un package nommé comme le projet)
│   └── main.py
├── tests/               # les tests (chapitre 7)
└── data/                # données locales (souvent ignorées par git)
```

### PEP 8, l'essentiel

[PEP 8](https://peps.python.org/pep-0008/) est la convention de style officielle. Le strict nécessaire pour démarrer :

- **Indentation : 4 espaces**, jamais de tabulations (VS Code gère ça par défaut).
- **Nommage** : `snake_case` pour variables et fonctions, `PascalCase` pour les classes, `MAJUSCULES` pour les constantes.
- **Lignes** ≤ 79 caractères (99 toléré en pratique ; les formateurs modernes coupent à 88).
- **Imports** en tête de fichier, un par ligne, en trois groupes séparés par une ligne vide : bibliothèque standard, packages tiers, code local.
- **Espaces** autour des opérateurs (`x = a + b`) et après les virgules ; pas d'espace juste après `(` ni avant `)`.
- Deux lignes vides entre les fonctions de niveau module.

Des outils formatent et vérifient tout ça automatiquement (`ruff`, `black`) — chapitre 7. En attendant, applique les règles à la main pour les intérioriser.

## Checklist de fin de chapitre

- [ ] Je navigue au terminal sans le Finder (`pwd`, `ls`, `cd`, `mkdir`, `mv`, `rm`).
- [ ] Je sais lire `ls -l` et rendre un script exécutable.
- [ ] `python3 --version` affiche un Python ≥ 3.12 installé via Homebrew.
- [ ] Je crée, active et désactive un venv, et j'utilise `pip freeze`/`requirements.txt`.
- [ ] VS Code : commande `code`, extension Python, interpréteur `.venv` sélectionné.
- [ ] J'ai exécuté un script en pas-à-pas avec un breakpoint.
- [ ] Je connais les règles PEP 8 de base (indentation, nommage, imports).
