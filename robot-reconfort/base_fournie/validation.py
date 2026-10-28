"""validation.py — Verification des fichiers d'entree (section 5.6)."""

from pathlib import Path
from reconfort_io import (
    ErreurFichier,
    charger_carte,
    charger_scenario,
    charger_armoire,
    charger_dictionnaire,
)

SYMBOLES_VALIDES = {"#", ".", "R", "A", "D", "P"}


def _verifier_type(valeur, types_attendus, nom_champ, contexte):
    """Verifie le type d'un champ."""
    # En Python bool est une sous-classe de int, on verifie que ce n'est pas un bool
    if types_attendus == int or (isinstance(types_attendus, tuple) and int in types_attendus):
        if isinstance(valeur, bool):
            raise ErreurFichier(f"{contexte} : '{nom_champ}' doit etre de type int, recu bool")

    if not isinstance(valeur, types_attendus):
        if isinstance(types_attendus, tuple):
            noms = ", ".join(t.__name__ for t in types_attendus)
        else:
            noms = types_attendus.__name__
        raise ErreurFichier(f"{contexte} : '{nom_champ}' doit etre de type {noms}, recu {type(valeur).__name__}")


def _verifier_champ(objet, nom_champ, types_attendus, contexte):
    """Verifie qu'un champ obligatoire existe et a le bon type."""
    if not isinstance(objet, dict):
        raise ErreurFichier(f"{contexte} doit etre un objet JSON")
    if nom_champ not in objet:
        raise ErreurFichier(f"{contexte} : champ obligatoire manquant '{nom_champ}'")
    valeur = objet[nom_champ]
    _verifier_type(valeur, types_attendus, nom_champ, contexte)
    return valeur


def _verifier_position(pos, contexte):
    """Verifie qu'une position est bien [ligne, colonne] avec des entiers."""
    if not isinstance(pos, (list, tuple)) or len(pos) != 2:
        raise ErreurFichier(f"{contexte} : position invalide {pos!r}, attendu [ligne, colonne]")
    l, c = pos[0], pos[1]
    if isinstance(l, bool) or not isinstance(l, int):
        raise ErreurFichier(f"{contexte} : la ligne doit etre un entier, recu {l!r}")
    if isinstance(c, bool) or not isinstance(c, int):
        raise ErreurFichier(f"{contexte} : la colonne doit etre un entier, recu {c!r}")
    return (l, c)


def _dans_grille(l, c, h, w):
    """Verifie si les coordonnees sont dans la grille."""
    return 0 <= l < h and 0 <= c < w


def valider_carte(carte):
    """Verifie la structure et le contenu d'une carte."""
    nom = carte.get("nom", "<sans nom>")
    ctx = f"carte {nom}"

    _verifier_champ(carte, "nom", str, ctx)
    if not carte["nom"].strip():
        raise ErreurFichier(f"{ctx} : nom vide")

    dim = _verifier_champ(carte, "dimensions", dict, ctx)
    h = _verifier_champ(dim, "hauteur", int, f"{ctx}.dimensions")
    w = _verifier_champ(dim, "largeur", int, f"{ctx}.dimensions")

    if h <= 0 or w <= 0:
        raise ErreurFichier(f"{ctx} : dimensions invalides ({h}x{w})")

    # Verification de la grille
    grille = _verifier_champ(carte, "grille", list, ctx)
    if len(grille) != h:
        raise ErreurFichier(f"{ctx} : dimensions incoherentes : hauteur {h}, reel {len(grille)}")

    for i, ligne in enumerate(grille):
        if not isinstance(ligne, str):
            raise ErreurFichier(f"{ctx} : ligne {i} doit etre une chaine")
        if len(ligne) != w:
            raise ErreurFichier(f"{ctx} : grille non rectangulaire : ligne {i} taille {len(ligne)}, attendu {w}")
        for car in ligne:
            if car not in SYMBOLES_VALIDES:
                raise ErreurFichier(f"{ctx} : symbole inconnu '{car}' dans la grille")

    # Verification du robot
    raw_robot = _verifier_champ(carte, "depart_robot", (list, tuple), ctx)
    lr, cr = _verifier_position(raw_robot, f"{ctx}.depart_robot")
    if not _dans_grille(lr, cr, h, w):
        raise ErreurFichier(f"{ctx} : depart_robot hors de la grille : [{lr}, {cr}]")
    if grille[lr][cr] != "R":
        raise ErreurFichier(f"{ctx} : symbole a depart_robot [{lr}, {cr}] est '{grille[lr][cr]}', attendu 'R'")

    # Verification de l'armoire
    arm_obj = _verifier_champ(carte, "armoire", dict, ctx)
    raw_arm = _verifier_champ(arm_obj, "position", (list, tuple), f"{ctx}.armoire")
    la, ca = _verifier_position(raw_arm, f"{ctx}.armoire.position")
    if not _dans_grille(la, ca, h, w):
        raise ErreurFichier(f"{ctx} : armoire hors de la grille : [{la}, {ca}]")
    if grille[la][ca] != "A":
        raise ErreurFichier(f"{ctx} : symbole armoire a [{la}, {ca}] est '{grille[la][ca]}', attendu 'A'")

    # Verification du dictionnaire
    dico_obj = _verifier_champ(carte, "dictionnaire", dict, ctx)
    raw_dico = _verifier_champ(dico_obj, "position", (list, tuple), f"{ctx}.dictionnaire")
    ld, cd = _verifier_position(raw_dico, f"{ctx}.dictionnaire.position")
    if not _dans_grille(ld, cd, h, w):
        raise ErreurFichier(f"{ctx} : dictionnaire hors de la grille : [{ld}, {cd}]")
    if grille[ld][cd] != "D":
        raise ErreurFichier(f"{ctx} : symbole dictionnaire a [{ld}, {cd}] est '{grille[ld][cd]}', attendu 'D'")

    # Verification des residents
    residents = _verifier_champ(carte, "residents", list, ctx)
    if len(residents) == 0:
        raise ErreurFichier(f"{ctx} : aucun resident declare")

    ids_vus = set()
    for idx, res in enumerate(residents):
        res_ctx = f"{ctx}.residents[{idx}]"
        _verifier_type(res, dict, f"residents[{idx}]", ctx)
        rid = _verifier_champ(res, "id", str, res_ctx)
        _verifier_champ(res, "nom", str, res_ctx)

        if not rid.strip():
            raise ErreurFichier(f"{res_ctx} : identifiant vide")
        if rid in ids_vus:
            raise ErreurFichier(f"{ctx} : deux residents ont le meme identifiant : '{rid}'")
        ids_vus.add(rid)

        raw_pos = _verifier_champ(res, "position", (list, tuple), res_ctx)
        lp, cp = _verifier_position(raw_pos, f"{res_ctx}.position")
        if not _dans_grille(lp, cp, h, w):
            raise ErreurFichier(f"{ctx} : resident '{rid}' hors de la grille : [{lp}, {cp}]")
        if grille[lp][cp] != "P":
            raise ErreurFichier(f"{ctx} : symbole resident '{rid}' a [{lp}, {cp}] est '{grille[lp][cp]}', attendu 'P'")

    # Verification du nombre de symboles sur la grille
    nb_r = sum(l.count("R") for l in grille)
    nb_a = sum(l.count("A") for l in grille)
    nb_d = sum(l.count("D") for l in grille)
    nb_p = sum(l.count("P") for l in grille)

    if nb_r != 1:
        raise ErreurFichier(f"{ctx} : la grille doit contenir exactement 1 'R', trouve {nb_r}")
    if nb_a != 1:
        raise ErreurFichier(f"{ctx} : la grille doit contenir exactement 1 'A', trouve {nb_a}")
    if nb_d != 1:
        raise ErreurFichier(f"{ctx} : la grille doit contenir exactement 1 'D', trouve {nb_d}")
    if nb_p != len(residents):
        raise ErreurFichier(f"{ctx} : {nb_p} symbole(s) 'P' dans la grille pour {len(residents)} resident(s)")


def valider_scenario(scenario):
    """Verifie le contenu d'un scenario."""
    nom = scenario.get("nom", "<sans nom>")
    ctx = f"scenario {nom}"

    _verifier_champ(scenario, "nom", str, ctx)
    _verifier_champ(scenario, "carte", str, ctx)
    _verifier_champ(scenario, "armoire", str, ctx)

    if not scenario["carte"].strip():
        raise ErreurFichier(f"{ctx} : nom de carte vide")
    if not scenario["armoire"].strip():
        raise ErreurFichier(f"{ctx} : nom d'armoire vide")

    demandes = _verifier_champ(scenario, "demandes", list, ctx)
    for idx, dem in enumerate(demandes):
        dem_ctx = f"{ctx}.demandes[{idx}]"
        _verifier_type(dem, dict, f"demandes[{idx}]", ctx)
        _verifier_champ(dem, "numero", int, dem_ctx)
        rid = _verifier_champ(dem, "resident", str, dem_ctx)
        msg = _verifier_champ(dem, "message", str, dem_ctx)
        if not rid.strip():
            raise ErreurFichier(f"{dem_ctx} : identifiant resident vide")
        if not isinstance(msg, str):
            raise ErreurFichier(f"{dem_ctx} : le message doit etre une chaine")


def valider_armoire(armoire):
    """Verifie l'armoire, ses casiers et ses etiquettes."""
    nom = armoire.get("nom", "<sans nom>")
    ctx = f"armoire {nom}"

    _verifier_champ(armoire, "nom", str, ctx)
    emotions = _verifier_champ(armoire, "emotions", list, ctx)
    intensites = _verifier_champ(armoire, "intensites", list, ctx)

    if len(emotions) == 0 or len(intensites) == 0:
        raise ErreurFichier(f"{ctx} : emotions ou intensites vides")

    nb_lignes = len(intensites)
    nb_colonnes = len(emotions)

    # Casier de depart
    raw_dep = _verifier_champ(armoire, "casier_depart", (list, tuple), ctx)
    ld, cd = _verifier_position(raw_dep, f"{ctx}.casier_depart")
    if not (0 <= ld < nb_lignes and 0 <= cd < nb_colonnes):
        raise ErreurFichier(f"{ctx} : casier_depart hors de l'armoire : [{ld}, {cd}]")

    # Verification des casiers
    casiers = _verifier_champ(armoire, "casiers", list, ctx)
    vus = set()

    for idx, c in enumerate(casiers):
        c_ctx = f"{ctx}.casiers[{idx}]"
        _verifier_type(c, dict, f"casiers[{idx}]", ctx)

        lig = _verifier_champ(c, "ligne", int, c_ctx)
        col = _verifier_champ(c, "colonne", int, c_ctx)
        emo = _verifier_champ(c, "emotion", str, c_ctx)
        inte = _verifier_champ(c, "intensite", str, c_ctx)
        _verifier_champ(c, "objet", (str, type(None)), c_ctx)

        # Hors bornes
        if not (0 <= lig < nb_lignes and 0 <= col < nb_colonnes):
            raise ErreurFichier(f"{ctx} : casier hors des dimensions : [{lig}, {col}]")

        # Doublon
        if (lig, col) in vus:
            raise ErreurFichier(f"{ctx} : casier en double a la position [{lig}, {col}]")
        vus.add((lig, col))

        # Coherence de l'etiquette avec (ligne, colonne)
        if emo != emotions[col] or inte != intensites[lig]:
            raise ErreurFichier(
                f"{ctx} : etiquette incoherente au casier [{lig}, {col}] : "
                f"attendu ({emotions[col]}, {intensites[lig]}), trouve ({emo}, {inte})"
            )


def valider_dictionnaire(dico):
    """Verifie le dictionnaire et l'unicite des mots."""
    nom = dico.get("nom", "<sans nom>")
    ctx = f"dictionnaire {nom}"

    _verifier_champ(dico, "nom", str, ctx)
    emotions = _verifier_champ(dico, "emotions", list, ctx)
    intensites = _verifier_champ(dico, "intensites", list, ctx)

    emotions_set = set(emotions)
    intensites_set = set(intensites)

    entrees = _verifier_champ(dico, "entrees", list, ctx)
    mots_vus = set()

    for idx, e in enumerate(entrees):
        e_ctx = f"{ctx}.entrees[{idx}]"
        _verifier_type(e, dict, f"entrees[{idx}]", ctx)

        formes = _verifier_champ(e, "formes", list, e_ctx)
        if len(formes) == 0:
            raise ErreurFichier(f"{e_ctx} : liste de formes vide")

        emo = _verifier_champ(e, "emotion", str, e_ctx)
        if emo not in emotions_set:
            raise ErreurFichier(f"{e_ctx} : emotion inconnue '{emo}'")

        inte = _verifier_champ(e, "intensite", str, e_ctx)
        if inte not in intensites_set:
            raise ErreurFichier(f"{e_ctx} : intensite inconnue '{inte}'")

        for mot in formes:
            if not isinstance(mot, str) or not mot.strip():
                raise ErreurFichier(f"{e_ctx} : forme invalide '{mot}'")
            if mot in mots_vus:
                raise ErreurFichier(f"{ctx} : meme mot dans deux entrees du dictionnaire : '{mot}'")
            mots_vus.add(mot)


def valider_coherence(carte, scenario, armoire=None, dico=None):
    """Verifie que le scenario et la carte sont compatibles."""
    if scenario["carte"] != carte["nom"]:
        raise ErreurFichier(
            f"incoherence : scenario pour '{scenario['carte']}', mais carte est '{carte['nom']}'"
        )

    residents_ids = {r["id"] for r in carte["residents"]}
    for dem in scenario["demandes"]:
        rid = dem["resident"]
        if rid not in residents_ids:
            raise ErreurFichier(f"demande {dem['numero']} pour resident inconnu '{rid}'")

    if armoire is not None and dico is not None:
        if armoire["emotions"] != dico["emotions"]:
            raise ErreurFichier("liste d'emotions differente entre armoire et dictionnaire")
        if armoire["intensites"] != dico["intensites"]:
            raise ErreurFichier("liste d'intensites differente entre armoire et dictionnaire")


def valider_tout(chemin_carte, chemin_scenario, dossier_donnees):
    """Charge et valide les 4 fichiers d'entree."""
    carte = charger_carte(chemin_carte)
    valider_carte(carte)

    scenario = charger_scenario(chemin_scenario)
    valider_scenario(scenario)

    dossier = Path(dossier_donnees)
    if not dossier.exists() or not dossier.is_dir():
        raise ErreurFichier(f"dossier de donnees introuvable : {dossier_donnees}")

    dico = charger_dictionnaire(dossier / "dictionnaire.json")
    valider_dictionnaire(dico)

    nom_armoire = scenario["armoire"]
    armoire = charger_armoire(dossier / f"{nom_armoire}.json")
    valider_armoire(armoire)

    valider_coherence(carte, scenario, armoire, dico)

    return carte, scenario, armoire, dico
