# robot/action.py
# Couche action : execute une action via le simulateur et la journalise.

def executer(sim, trace, demande, action, argument, perception_courante, contenu_casier_courant):
    """Execute une action et l'enregistre dans la trace.
    
    IMPORTANT : l'enonce exige que position et casier soient ceux AVANT l'action.
    On les capture donc avant d'appeler sim.appliquer().
    """
    pos_avant    = sim.position
    casier_avant = sim.selecteur

    sim.appliquer(action, argument)

    trace.ajouter_pas(
        demande = demande,
        position = pos_avant,
        casier = casier_avant,
        action = action,
        argument = argument,
        perception = perception_courante,
        contenu_casier = contenu_casier_courant,
    )