DELTAS = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "O": (0, -1),
}

DIRECTIONS = ("N", "S", "E", "O")


def deplacer(pos, direction):
    """Calcule la position apres un deplacement dans une direction."""
    if direction not in DELTAS:
        raise ValueError("Direction invalide : " + str(direction))
    dl, dc = DELTAS[direction]
    return (pos[0] + dl, pos[1] + dc)


def voisins(pos):
    """Retourne la liste des 4 voisins dans l'ordre N, S, E, O."""
    l = pos[0]
    c = pos[1]
    res = []
    for d in DIRECTIONS:
        dl, dc = DELTAS[d]
        res.append((l + dl, c + dc))
    return res


def voisins_avec_directions(pos):
    """Retourne la liste des (direction, voisin)."""
    l = pos[0]
    c = pos[1]
    res = []
    for d in DIRECTIONS:
        dl, dc = DELTAS[d]
        res.append((d, (l + dl, c + dc)))
    return res


def direction_entre(pos1, pos2):
    """Retourne la direction ('N', 'S', 'E', 'O') pour aller de pos1 a pos2."""
    dl = pos2[0] - pos1[0]
    dc = pos2[1] - pos1[1]
    for d in DELTAS:
        if DELTAS[d] == (dl, dc):
            return d
    raise ValueError("Les positions ne sont pas adjacentes.")
