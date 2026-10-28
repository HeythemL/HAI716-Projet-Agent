"""agent.py — Point d'entree du robot de reconfort.

Usage :
    python agent.py <carte.json> <scenario.json> <dossier_donnees> <trace.json>
"""
import sys
from pathlib import Path

# on s'assure que base_fournie est dans le chemin Python
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reconfort_io import (
    charger_carte, charger_armoire, charger_dictionnaire,
    charger_scenario, ErreurFichier, Trace
)
from monde.simulateur import Simulateur
from robot.memoire import CarteMentale
from robot.lecture_emotion import LecteurEmotion
from robot.decision import Robot
from robot import perception as perc
from robot import action as act
from validation import valider_tout


def main():
    # ---- arguments -------------------------------------------------------
    if len(sys.argv) != 5:
        print("Usage: python agent.py <carte> <scenario> <donnees> <trace>",
              file=sys.stderr)
        sys.exit(2)

    chemin_carte, chemin_scenario, dossier_donnees, chemin_trace = sys.argv[1:]

    # ---- chargement et validation des fichiers ---------------------------
    try:
        carte_data, scenario_data, armoire_data, dico_data = valider_tout(
            chemin_carte, chemin_scenario, dossier_donnees
        )
    except ErreurFichier as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erreur inattendue : {e}", file=sys.stderr)
        sys.exit(1)

    # ---- construction des composants ------------------------------------
    sim = Simulateur(carte_data, armoire_data)

    pos_armoire = tuple(carte_data["armoire"]["position"])
    pos_dico    = tuple(carte_data["dictionnaire"]["position"])
    residents   = {r["id"]: tuple(r["position"]) for r in carte_data["residents"]}

    carte_mentale = CarteMentale(
        hauteur      = carte_data["dimensions"]["hauteur"],
        largeur      = carte_data["dimensions"]["largeur"],
        armoire      = pos_armoire,
        dictionnaire = pos_dico,
        residents    = list(residents.values()),
    )

    lecteur = LecteurEmotion(dico_data)
    robot   = Robot(carte_mentale, lecteur, pos_armoire, pos_dico, residents)

    trace = Trace(
        nom_carte    = carte_data["nom"],
        nom_scenario = scenario_data["nom"],
        equipe       = [],  # a remplir dans rendu.json
    )

    # ---- boucle principale : une demande a la fois ----------------------
    H = carte_data["dimensions"]["hauteur"]
    L = carte_data["dimensions"]["largeur"]
    MAX_PAS = 5 * H * L  # securite contre les boucles infinies

    for demande_data in scenario_data["demandes"]:
        num   = demande_data["numero"]
        rid   = demande_data["resident"]
        msg   = demande_data["message"]

        robot.nouvelle_demande(msg, rid)

        for _ in range(MAX_PAS):
            if robot.est_termine:
                break

            # 1. perception
            perception_courante  = perc.percevoir(sim)
            contenu_courant      = perc.contenu_casier(sim)

            # 2. mise a jour memoire
            robot.mettre_a_jour(sim.position, perception_courante,
                                sim.selecteur, contenu_courant)

            # 3. decision
            action, argument = robot.decider(sim.position, sim.selecteur)

            # 4. action + log trace
            act.executer(sim, trace, num, action, argument,
                         perception_courante, contenu_courant)

        # si le robot n'a pas fini dans MAX_PAS, on force l'echec
        if not robot.est_termine:
            robot.etat        = "ECHEC"
            robot.motif_echec = "resident inaccessible"
            # reset objet porte pour la prochaine demande
            sim.objet_porte = None

        # enregistrement de la livraison
        if robot.est_succes:
            trace.ajouter_livraison(
                demande       = num,
                resident      = rid,
                emotion       = robot.emotion,
                intensite     = robot.intensite,
                casier_choisi = robot.casier_choisi,
                repli         = robot.repli,
                objet         = robot.objet_porte,
                succes        = True,
            )
        else:
            # si le robot porte encore un objet (echec apres PRENDRE), on le repose
            if sim.objet_porte is not None:
                sim.objet_porte = None
            trace.ajouter_livraison(
                demande       = num,
                resident      = rid,
                emotion       = robot.emotion,
                intensite     = robot.intensite,
                casier_choisi = robot.casier_choisi,
                repli         = robot.repli,
                objet         = None,
                succes        = False,
                motif_echec   = robot.motif_echec or "resident inaccessible",
            )

    # ---- ecriture de la trace -------------------------------------------
    trace.ecrire(chemin_trace)
    print(f"Trace ecrite dans {chemin_trace}")


if __name__ == "__main__":
    main()
