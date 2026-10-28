"""outils/verifier_trace.py — Verification des traces."""

import json
import sys
from pathlib import Path

DOSSIER_BASE = Path(__file__).resolve().parent.parent
if str(DOSSIER_BASE) not in sys.path:
    sys.path.insert(0, str(DOSSIER_BASE))

from robot import roue


class ErreurTrace(Exception):
    """Erreur levee quand la trace n'est pas conforme."""
    pass


def deplacer(pos, direction):
    """Calcule la case voisine dans la direction donnee."""
    l, c = pos
    if direction == "N":
        return (l - 1, c)
    elif direction == "S":
        return (l + 1, c)
    elif direction == "E":
        return (l, c + 1)
    elif direction == "O":
        return (l, c - 1)
    raise ErreurTrace(f"Direction invalide : {direction}")


def est_adjacent(p1, p2):
    """Verifie si deux cases se touchent (haut, bas, gauche, droite)."""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) == 1


def calculer_perception(pos_robot, grille, h, w):
    """Calcule ce que le robot doit reellement voir autour de lui."""
    perception = {}
    for d in ("N", "S", "E", "O"):
        vl, vc = deplacer(pos_robot, d)
        if vl < 0 or vl >= h or vc < 0 or vc >= w:
            perception[d] = "mur"
        else:
            symbole = grille[vl][vc]
            if symbole == "#":
                perception[d] = "mur"
            elif symbole in (".", "R"):
                perception[d] = "libre"
            elif symbole == "A":
                perception[d] = "armoire"
            elif symbole == "D":
                perception[d] = "dictionnaire"
            elif symbole == "P":
                perception[d] = "resident"
            else:
                perception[d] = "mur"
    return perception


def verifier_trace(carte_data, scenario_data, armoire_data, trace_data):
    """Rejoue la trace pas a pas pour tout verifier."""
    # 1. En-tete
    if trace_data.get("format") != "robot-reconfort/trace":
        raise ErreurTrace(f"Format invalide : {trace_data.get('format')}")
    if trace_data.get("version") != 1:
        raise ErreurTrace(f"Version invalide : {trace_data.get('version')}")
    if trace_data.get("carte") != carte_data["nom"]:
        raise ErreurTrace("Nom de carte incoherent dans la trace")
    if trace_data.get("scenario") != scenario_data["nom"]:
        raise ErreurTrace("Nom de scenario incoherent dans la trace")

    h = carte_data["dimensions"]["hauteur"]
    w = carte_data["dimensions"]["largeur"]
    grille = carte_data["grille"]
    pos_armoire = tuple(carte_data["armoire"]["position"])
    pos_dico = tuple(carte_data["dictionnaire"]["position"])

    residents_pos = {r["id"]: tuple(r["position"]) for r in carte_data["residents"]}
    demandes_scenario = {d["numero"]: d["resident"] for d in scenario_data["demandes"]}
    contenu_armoire = {(c["ligne"], c["colonne"]): c["objet"] for c in armoire_data["casiers"]}

    # Position de depart du robot et du selecteur
    pos_robot = tuple(carte_data["depart_robot"])
    pos_selecteur = tuple(armoire_data["casier_depart"])
    objet_porte = None
    casiers_vus = {}

    pas_liste = trace_data.get("pas", [])
    if not pas_liste:
        raise ErreurTrace("Aucun pas dans la trace")

    # 2. Verification de chaque pas
    for t_attendu, pas in enumerate(pas_liste):
        t = pas.get("t")
        if t != t_attendu:
            raise ErreurTrace(f"Pas t={t} : mauvais indice (attendu {t_attendu})")

        num_dem = pas.get("demande")
        if num_dem not in demandes_scenario:
            raise ErreurTrace(f"Pas t={t} : demande inconnue {num_dem}")

        # Position et casier avant l'action
        if tuple(pas.get("position", [])) != pos_robot:
            raise ErreurTrace(f"Pas t={t} : position robot fausse dans la trace")
        if tuple(pas.get("casier", [])) != pos_selecteur:
            raise ErreurTrace(f"Pas t={t} : position casier fausse dans la trace")

        # Verification des perceptions
        perc_reelle = calculer_perception(pos_robot, grille, h, w)
        for d in ("N", "S", "E", "O"):
            if pas.get("perception", {}).get(d) != perc_reelle[d]:
                raise ErreurTrace(f"Pas t={t} : perception falsifiee en {d}")

        # Verification du casier vu
        devant_armoire = est_adjacent(pos_robot, pos_armoire)
        contenu_trace = pas.get("contenu_casier")
        if devant_armoire:
            reel = contenu_armoire.get(pos_selecteur, None)
            if contenu_trace != reel:
                raise ErreurTrace(f"Pas t={t} : faux contenu de casier a {pos_selecteur}")
            casiers_vus[pos_selecteur] = reel
        else:
            if contenu_trace is not None:
                raise ErreurTrace(f"Pas t={t} : contenu_casier doit etre null hors de l'armoire")

        # Application de l'action
        action = pas.get("action")
        arg = pas.get("argument")

        if action == "AVANCER":
            if arg not in ("N", "S", "E", "O"):
                raise ErreurTrace(f"Pas t={t} : direction invalide pour AVANCER")
            dest = deplacer(pos_robot, arg)
            if dest[0] < 0 or dest[0] >= h or dest[1] < 0 or dest[1] >= w:
                raise ErreurTrace(f"Pas t={t} : AVANCER hors grille")
            if grille[dest[0]][dest[1]] not in (".", "R"):
                raise ErreurTrace(f"Pas t={t} : case non traversable pour AVANCER")
            pos_robot = dest

        elif action == "CONSULTER":
            if not est_adjacent(pos_robot, pos_dico):
                raise ErreurTrace(f"Pas t={t} : CONSULTER trop loin du dictionnaire")

        elif action == "CHERCHER":
            if not devant_armoire:
                raise ErreurTrace(f"Pas t={t} : CHERCHER trop loin de l'armoire")
            lig, col = pos_selecteur
            if arg == "N":
                if lig == 0:
                    raise ErreurTrace(f"Pas t={t} : CHERCHER N impossible sur la premiere ligne")
                lig -= 1
            elif arg == "S":
                if lig == 2:
                    raise ErreurTrace(f"Pas t={t} : CHERCHER S impossible sur la derniere ligne")
                lig += 1
            elif arg == "E":
                col = (col + 1) % 8
            elif arg == "O":
                col = (col - 1) % 8
            else:
                raise ErreurTrace(f"Pas t={t} : direction invalide pour CHERCHER")
            pos_selecteur = (lig, col)

        elif action == "PRENDRE":
            if not devant_armoire:
                raise ErreurTrace(f"Pas t={t} : PRENDRE hors de l'armoire")
            if objet_porte is not None:
                raise ErreurTrace(f"Pas t={t} : robot porte deja un objet")
            contenu = contenu_armoire.get(pos_selecteur, None)
            if contenu is None:
                raise ErreurTrace(f"Pas t={t} : casier vide pour PRENDRE")
            if arg != contenu:
                raise ErreurTrace(f"Pas t={t} : mauvais nom d'objet pour PRENDRE")
            objet_porte = arg

        elif action == "DONNER":
            if objet_porte is None:
                raise ErreurTrace(f"Pas t={t} : DONNER mais robot a les mains vides")
            if arg != objet_porte:
                raise ErreurTrace(f"Pas t={t} : mauvais objet pour DONNER")
            pos_res = residents_pos[demandes_scenario[num_dem]]
            if not est_adjacent(pos_robot, pos_res):
                raise ErreurTrace(f"Pas t={t} : DONNER trop loin du resident")
            objet_porte = None

        elif action == "ATTENDRE":
            pass
        else:
            raise ErreurTrace(f"Pas t={t} : action inconnue {action!r}")

    # 3. Verification des livraisons
    livraisons = trace_data.get("livraisons", [])
    if len(livraisons) != len(scenario_data["demandes"]):
        raise ErreurTrace("Nombre de livraisons incoherent")

    for i, liv in enumerate(livraisons):
        dem = scenario_data["demandes"][i]
        if liv.get("demande") != dem["numero"] or liv.get("resident") != dem["resident"]:
            raise ErreurTrace("Incoherence sur une livraison")

        if liv.get("succes"):
            casier = tuple(liv.get("casier_choisi", []))
            candidats = roue.candidats(liv.get("emotion"), liv.get("intensite"))
            idx_choisi = None
            for idx, c in enumerate(candidats):
                if c.casier == casier:
                    idx_choisi = idx
                    break

            if idx_choisi is None:
                raise ErreurTrace("Casier choisi n'est pas dans les 15 candidats")

            # Verifie que tous les candidats plus prioritaires etaient bien vus vides
            for idx in range(idx_choisi):
                prioritaire = candidats[idx].casier
                if prioritaire not in casiers_vus:
                    raise ErreurTrace(f"Casier prioritaire {prioritaire} non vu avant de prendre un repli")
                if casiers_vus[prioritaire] is not None:
                    raise ErreurTrace(f"Casier prioritaire {prioritaire} contenait un objet mais a ete ignore")

            if liv.get("repli") != candidats[idx_choisi].repli:
                raise ErreurTrace("Etiquette de repli incorrecte")
        else:
            motif = liv.get("motif_echec")
            if motif not in ("resident inaccessible", "armoire vide", "emotion indeterminee"):
                raise ErreurTrace(f"Motif d'echec invalide : {motif}")

    # 4. Verification du resume
    res = trace_data.get("resume", {})
    nb_ok = sum(1 for l in livraisons if l.get("succes"))
    nb_ko = sum(1 for l in livraisons if not l.get("succes"))

    if res.get("demandes") != len(scenario_data["demandes"]):
        raise ErreurTrace("Resume : nombre de demandes faux")
    if res.get("reussies") != nb_ok:
        raise ErreurTrace("Resume : nombre de reussites faux")
    if res.get("echecs") != nb_ko:
        raise ErreurTrace("Resume : nombre d'echecs faux")
    if res.get("pas_total") != len(pas_liste):
        raise ErreurTrace("Resume : pas_total faux")

    return True


def main():
    if len(sys.argv) != 5:
        print("Usage: python outils/verifier_trace.py <carte.json> <scenario.json> <donnees> <trace.json>")
        sys.exit(2)

    chemin_carte, chemin_scenario, chemin_donnees, chemin_trace = sys.argv[1:]

    try:
        with open(chemin_carte, "r", encoding="utf-8") as f:
            carte = json.load(f)
        with open(chemin_scenario, "r", encoding="utf-8") as f:
            scenario = json.load(f)

        p = Path(chemin_donnees)
        if p.is_dir():
            fichier_armoire = p / f"{scenario.get('armoire', 'armoire_standard')}.json"
        else:
            fichier_armoire = p

        with open(fichier_armoire, "r", encoding="utf-8") as f:
            armoire = json.load(f)
        with open(chemin_trace, "r", encoding="utf-8") as f:
            trace = json.load(f)

        verifier_trace(carte, scenario, armoire, trace)

        print(f"Trace valide : {chemin_trace}")
        print(f"  - {len(trace['pas'])} pas verifies")
        print(f"  - {len(trace['livraisons'])} livraisons conformes")
        sys.exit(0)

    except ErreurTrace as e:
        print(f"Erreur trace : {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
