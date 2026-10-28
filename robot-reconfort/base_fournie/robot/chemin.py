from collections import deque
from robot import geometrie


def plus_court_chemin(depart, arrivees, est_traversable):
    """BFS : trouve le chemin le plus court de depart vers une des cases dans arrivees.
    
    Retourne la liste de cases (depart inclus, arrivee incluse), ou None si impossible.
    """
    arrivees = set(arrivees)

    # cas trivial : on est deja sur une cible
    if depart in arrivees:
        return [depart]

    # predecesseur[case] = d'ou on vient (None pour le depart)
    # sert aussi a marquer les cases deja visitees
    predecesseur = {depart: None}
    file = deque([depart])

    while file:
        courant = file.popleft()  # on prend le plus ancien (FIFO = BFS)

        for voisin in geometrie.voisins(courant):
            if voisin in predecesseur:
                continue  # deja visite
            if voisin in arrivees:
                # arrive ! on remonte le chemin
                predecesseur[voisin] = courant
                return _reconstruire(predecesseur, voisin)
            if not est_traversable(voisin):
                continue  # mur ou obstacle, on passe
            predecesseur[voisin] = courant
            file.append(voisin)

    return None  # file vide = pas de chemin = resident inaccessible


def _reconstruire(predecesseur, arrivee):
    """Remonte la chaine predecesseur -> predecesseur pour retrouver le chemin."""
    chemin = []
    case = arrivee
    while case is not None:
        chemin.append(case)
        case = predecesseur[case]
    chemin.reverse()
    return chemin


def premier_pas(depart, arrivees, est_traversable):
    """Renvoie juste la prochaine case a atteindre (chemin[1]), ou None."""
    chemin = plus_court_chemin(depart, arrivees, est_traversable)
    if chemin is None or len(chemin) < 2:
        return None
    return chemin[1]


def cases_adjacentes_libres(position_obstacle, est_traversable):
    """Retourne les cases libres autour d'un obstacle (armoire, dico, resident).
    
    Le robot ne peut pas aller SUR l'obstacle, il doit s'en approcher d'a cote.
    """
    return {
        voisin
        for voisin in geometrie.voisins(position_obstacle)
        if est_traversable(voisin)
    }
