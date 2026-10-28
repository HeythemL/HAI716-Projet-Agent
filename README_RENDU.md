# Robot de réconfort — Projet HAI716

Projet de semestre — Master Informatique.
Un robot à perception locale consulte un dictionnaire, fouille une armoire selon la roue de Plutchik et rapporte un objet de réconfort à un résident.

- **Langage** : Python 3.9+
- **Dépendances** : Aucune dépendance externe (uniquement la bibliothèque standard : `json`, `pathlib`, `collections`, `unicodedata`, `sys`, `unittest`, `subprocess`).

---

## 1. Lancer

Le programme principal respecte strictement le contrat d'appel à 4 arguments :

```bash
python agent.py <carte.json> <scenario.json> <dossier_donnees> <trace_sortie.json>
```

### Exemple :
```bash
python agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sorties/trace_01.json
```

---

## 2. Tester

La suite de tests unitaires et de validation se lance avec la commande standard :

```bash
python -m unittest discover -s tests
```

### Couverture des tests (65 tests) :
- **Logique pure (`tests/test_logique.py` — 31 tests)** :
  - Déplacements géométriques et calcul des 4 voisins orthogonaux.
  - Normalisation lexicale et reconnaissance du premier mot dans le dictionnaire.
  - Calcul des distances sur la roue de Plutchik et ordonnancement des 15 candidats.
  - Déplacement cyclique du sélecteur (colonnes $0 \leftrightarrow 7$ modulo 8, blocage des lignes $0$ et $2$).
  - Algorithme de recherche de chemin (BFS) et replanification dynamique après découverte d'un mur.
- **Validation section 5.6 (`tests/test_validation.py` — 29 tests)** :
  - Tests en sous-processus (`subprocess`) sur 25 fichiers et configurations cassés : fichiers absents, non-UTF-8, JSON invalide, champs manquants, coordonnées hors grille, incohérences carte/scénario, casiers en double ou mal étiquetés, etc.
  - Vérification du code de sortie non nul (`1` pour erreur de données, `2` pour arguments invalides), message d'erreur sur `stderr`, absence de traceback Python et aucun fichier de trace écrit.
- **Correcteur de trace (`tests/test_verifier_trace.py` — 5 tests)** :
  - Rejeu pas à pas de la trace et détection automatique des falsifications de perceptions, déplacements illégaux, casiers non vus ou résumés erronés.

---

## 3. Organisation du code

L'architecture sépare strictement le modèle du monde physique et l'agent autonome :

| Fichier / Dossier | Rôle |
|---|---|
| `agent.py` | Point d'entrée en ligne de commande, orchestration de la boucle de décision. |
| `validation.py` | Validation préalable stricte de tous les fichiers d'entrée (section 5.6). |
| `reconfort_io.py` | Module fourni de lecture JSON et d'enregistrement de la `Trace`. |
| `monde/simulateur.py` | **Seul fichier** lisant `grille` et `objet` ; simule la réalité physique et répond aux perceptions. |
| `robot/perception.py` | Couche d'observation locale (4 cases adjacentes et casier courant). |
| `robot/memoire.py` | Carte mentale de l'agent (hypothèse optimiste : l'inconnu est supposé libre). |
| `robot/decision.py` | Machine à états finis régissant le comportement de l'agent pour chaque demande. |
| `robot/action.py` | Exécution des actions sur le simulateur et journalisation dans la trace. |
| `robot/chemin.py` | Recherche de chemin en largeur (BFS) avec dictionnaire de prédécesseurs. |
| `robot/roue.py` | Calcul des distances de Plutchik et tri des 15 candidats de repli. |
| `robot/selecteur.py` | Déplacements et plus court chemin du sélecteur de l'armoire (bouclage modulo 8). |
| `robot/lecture_emotion.py` | Normalisation du texte et recherche du premier mot dans le dictionnaire. |
| `outils/verifier_trace.py` | Grader / vérificateur de trace indépendant validant les traces selon le barème. |
| `outils/visualiser.py` | Rejeu visuel de la trace dans le terminal (pour la démonstration). |
| `tests/` | Ensemble des 65 tests unitaires et sous-dossier `fichiers_casses/`. |

---

## 4. État du projet

### Ce qui marche :
- **Perception strictement locale** : Le robot ne lit jamais la grille complète et découvre les murs au fur et à mesure.
- **Replanification dynamique** : En cas de mur imprévu, la carte mentale est mise à jour immédiatement et le BFS recalcule le chemin sans bloquer le robot.
- **Respect absolu des règles de repli** : Le robot n'utilise un casier de repli qu'après avoir visité et constaté vides tous les casiers de priorité supérieure.
- **Persistance entre les demandes** : La position du robot, sa carte mentale et la position du sélecteur persistent d'une demande à l'autre au sein d'un même scénario.
- **Validation robuste (2 pts)** : Tous les fichiers mal formés ou incohérents sont rejetés proprement avec message d'erreur et sans trace résiduelle.
- **Validation des 5 scénarios** : Les scénarios 01 à 05 s'exécutent avec 100% de succès et passent avec succès le vérificateur de trace.

### Ce qui ne marche pas / limites honnêtes :
- **Replanification complète à chaque tick** : L'agent relance un BFS à chaque pas au lieu de réparer localement le plan existant. Bien que rapide sur les cartes testées ($< 1$ ms par pas), ce choix est sous-optimal sur des cartes géantes.
- **Itinéraire du sélecteur myope** : Le sélecteur calcule le plus court chemin vers le *premier* candidat non vu sans anticiper les candidats suivants. Si ce casier s'avère vide, il doit recalculer une nouvelle route, ce qui peut engendrer des allers-retours évitables.
- **Coût d'exploration pour prouver un résident inaccessible** : Lorsqu'un résident est enfermé, le robot ne déclare l'échec qu'après avoir exploré les couloirs jusqu'à ce que sa carte mentale ne contienne plus aucun passage théorique libre vers le résident, ce qui consomme de nombreux pas.

---

## 5. Vidéo

Fichier vidéo joint : `demo.mp4` (durée inférieure à 1 min 30 s, capture du terminal montrant la navigation et l'évitement d'un mur imprévu).
Également déclarée dans le fichier `rendu.json`.
