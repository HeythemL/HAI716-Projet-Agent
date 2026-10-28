# robot/perception.py
# Couche perception : demande au simulateur ce que le robot voit.

def percevoir(sim):
    """Retourne les 4 cases adjacentes {direction: type}."""
    return sim.percevoir()

def contenu_casier(sim):
    """Retourne l'objet dans le casier courant (None si pas adjacent ou casier vide)."""
    return sim.contenu_casier_courant()
