NB_LIGNES = 3
NB_COLONNES = 8

DIRECTIONS_VALIDES = ("N", "S", "E", "O")


def est_deplacement_valide(position, direction):
    """Verifie si le mouvement est autorise."""
    ligne = position[0]
    if direction == "N":
        return ligne > 0
    if direction == "S":
        return ligne < NB_LIGNES - 1
    if direction in ("E", "O"):
        return True
    return False


def deplacer(position, direction):
    """Deplace le selecteur d'une case (les colonnes bouclent modulo 8)."""
    ligne = position[0]
    colonne = position[1]

    if direction == "N":
        if ligne <= 0:
            raise ValueError("Deplacement N impossible en ligne 0")
        return (ligne - 1, colonne)
    elif direction == "S":
        if ligne >= NB_LIGNES - 1:
            raise ValueError("Deplacement S impossible en ligne 2")
        return (ligne + 1, colonne)
    elif direction == "E":
        return (ligne, (colonne + 1) % NB_COLONNES)
    elif direction == "O":
        return (ligne, (colonne - 1) % NB_COLONNES)
    else:
        raise ValueError("Direction inconnue : " + str(direction))


def mouvements_verticaux(ligne_dep, ligne_arr):
    """Calcule les deplacements N ou S entre deux lignes."""
    diff = ligne_arr - ligne_dep
    if diff > 0:
        return ["S"] * diff
    elif diff < 0:
        return ["N"] * (-diff)
    return []


def mouvements_horizontaux(colonne_dep, colonne_arr):
    """Calcule les deplacements E ou O entre deux colonnes (bouclage)."""
    a = (colonne_arr - colonne_dep) % NB_COLONNES
    if a <= NB_COLONNES - a:
        return ["E"] * a
    else:
        return ["O"] * (NB_COLONNES - a)


def distance(depart, arrivee):
    """Calcule le nombre de pas minimal entre deux casiers."""
    nb_v = abs(arrivee[0] - depart[0])
    a = (arrivee[1] - depart[1]) % NB_COLONNES
    if a <= NB_COLONNES - a:
        nb_h = a
    else:
        nb_h = NB_COLONNES - a
    return nb_v + nb_h


def route(depart, arrivee, vertical_dabord=True):
    """Calcule la liste des mouvements pour aller d'un casier a l'autre."""
    mouv_v = mouvements_verticaux(depart[0], arrivee[0])
    mouv_h = mouvements_horizontaux(depart[1], arrivee[1])
    if vertical_dabord:
        return mouv_v + mouv_h
    else:
        return mouv_h + mouv_v


def positions_traversees(depart, mouvements):
    """Retourne la liste des positions visitees en faisant les mouvements."""
    pos = (depart[0], depart[1])
    visitees = []
    for m in mouvements:
        pos = deplacer(pos, m)
        visitees.append(pos)
    return visitees


class Selecteur:
    """Gere la position du selecteur dans l'armoire."""

    def __init__(self, position=(1, 0)):
        self.position = (position[0], position[1])

    @property
    def ligne(self):
        return self.position[0]

    @property
    def colonne(self):
        return self.position[1]

    @property
    def casier(self):
        return self.position

    def peut_avancer(self, direction):
        return est_deplacement_valide(self.position, direction)

    def avancer(self, direction):
        self.position = deplacer(self.position, direction)
        return self.position

    def chemin_vers(self, cible, vertical_dabord=True):
        return route(self.position, cible, vertical_dabord=vertical_dabord)
