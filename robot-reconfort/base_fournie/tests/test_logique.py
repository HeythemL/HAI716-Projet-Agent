"""Tests unitaires pour les modules de logique pure :
- geometrie.py
- lecture_emotion.py (section 6.1 et item 3 section 8)
- roue.py (section 6.2, annexe A, annexe C.5 et item 5 section 8)
- selecteur.py (annexe B.7, annexe C et item 4 section 8)
- chemin.py (BFS, items 1, 2, 7 section 8)
"""

import sys
from pathlib import Path
import unittest

# Assurer l'accès aux modules de base_fournie
DOSSIER_BASE = Path(__file__).resolve().parent.parent
if str(DOSSIER_BASE) not in sys.path:
    sys.path.insert(0, str(DOSSIER_BASE))

from robot import geometrie, lecture_emotion, roue, selecteur, chemin


class TestGeometrie(unittest.TestCase):
    def test_deltas(self):
        self.assertEqual(geometrie.DELTAS["N"], (-1, 0))
        self.assertEqual(geometrie.DELTAS["S"], (1, 0))
        self.assertEqual(geometrie.DELTAS["E"], (0, 1))
        self.assertEqual(geometrie.DELTAS["O"], (0, -1))

    def test_voisins(self):
        v = geometrie.voisins((6, 4))
        self.assertEqual(v, [(5, 4), (7, 4), (6, 5), (6, 3)])

    def test_deplacer(self):
        self.assertEqual(geometrie.deplacer((2, 3), "N"), (1, 3))
        self.assertEqual(geometrie.deplacer((2, 3), "S"), (3, 3))
        self.assertEqual(geometrie.deplacer((2, 3), "E"), (2, 4))
        self.assertEqual(geometrie.deplacer((2, 3), "O"), (2, 2))
        with self.assertRaises(ValueError):
            geometrie.deplacer((2, 3), "X")

    def test_direction_entre(self):
        self.assertEqual(geometrie.direction_entre((2, 3), (1, 3)), "N")
        self.assertEqual(geometrie.direction_entre((2, 3), (3, 3)), "S")
        self.assertEqual(geometrie.direction_entre((2, 3), (2, 4)), "E")
        self.assertEqual(geometrie.direction_entre((2, 3), (2, 2)), "O")
        with self.assertRaises(ValueError):
            geometrie.direction_entre((2, 3), (4, 3))


class TestLectureEmotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chemin_dict = DOSSIER_BASE / "donnees" / "dictionnaire.json"
        cls.lecteur = lecture_emotion.LecteurEmotion(chemin_dict)
        cls.index = cls.lecteur.index

    def test_normaliser(self):
        mots = lecture_emotion.normaliser("Je suis TERRIFIEE, vraiment !")
        self.assertEqual(mots, ["je", "suis", "terrifiee", "vraiment"])

    def test_un_message_par_emotion(self):
        """Item 3 de la section 8 : tester un message pour chacune des 8 émotions."""
        exemples = [
            ("Je ressens une joie immense aujourd'hui.", "joie"),
            ("J'ai une confiance totale en votre aide.", "confiance"),
            ("J'ai très peur de ce bruit étrange.", "peur"),
            ("Quelle surprise inattendue ce matin !", "surprise"),
            ("Je suis si triste ce soir...", "tristesse"),
            ("Ce plat m'inspire un profond degout.", "degout"),
            ("Je suis pris d'une grande colere !", "colere"),
            ("Je suis très impatient pour demain.", "anticipation"),
        ]
        for msg, emotion_attendue in exemples:
            res = self.lecteur.identifier(msg)
            self.assertIsNotNone(res, f"Émotion non trouvée pour le message : {msg}")
            self.assertEqual(res[0], emotion_attendue, f"Émotion incorrecte pour : {msg}")

    def test_premier_mot_qui_gagne(self):
        """Exemple de l'énoncé section 6.1 :
        'Je suis sidéré, la télévision s'est allumée toute seule.'
        'sidere' -> surprise / forte
        'seule' arrive après -> ne compte pas.
        """
        msg = "Je suis sidéré, la télévision s'est allumée toute seule."
        res = self.lecteur.identifier(msg)
        self.assertEqual(res, ("surprise", "forte"))

    def test_deux_mots_connus_ordre(self):
        # 'triste' puis 'joie' -> 'triste' gagne
        msg = "Parfois je suis triste, parfois plein de joie."
        res = self.lecteur.identifier(msg)
        self.assertEqual(res, ("tristesse", "moyenne"))

    def test_message_aucun_mot_reconnu(self):
        """Item 3 section 8 : un message sans aucun mot reconnu retourne None."""
        msg = "Bonjour, il fait beau dehors aujourd'hui."
        res = self.lecteur.identifier(msg)
        self.assertIsNone(res)


class TestRoue(unittest.TestCase):
    def test_distance_roue(self):
        # Ordre : joie (0), confiance (1), peur (2), surprise (3), tristesse (4), degout (5), colere (6), anticipation (7)
        self.assertEqual(roue.distance("joie", "joie"), 0)
        self.assertEqual(roue.distance("joie", "confiance"), 1)
        self.assertEqual(roue.distance("joie", "anticipation"), 1)
        self.assertEqual(roue.distance("anticipation", "joie"), 1)
        self.assertEqual(roue.distance("joie", "peur"), 2)
        self.assertEqual(roue.distance("joie", "tristesse"), 4)  # Diamétralement opposé
        self.assertEqual(roue.distance("surprise", "tristesse"), 1)
        self.assertEqual(roue.distance("surprise", "peur"), 1)
        self.assertEqual(roue.distance("surprise", "degout"), 2)
        self.assertEqual(roue.distance("surprise", "confiance"), 2)

    def test_candidats_surprise_forte_annexe_c5(self):
        """Vérification stricte contre Annexe C.5 :
        Demande surprise / forte :
        Rang 1 : [2, 3] surprise / forte (repli = aucun)
        Rang 2 : [1, 3] surprise / moyenne (repli = intensite)
        Rang 3 : [0, 3] surprise / faible (repli = intensite)
        Rang 4 : [2, 4] tristesse / forte (repli = voisine_1)
        Rang 5 : [2, 2] peur / forte (repli = voisine_1)
        """
        cands = roue.candidats("surprise", "forte")
        self.assertEqual(len(cands), 15)

        # Rang 1
        self.assertEqual(cands[0].casier, (2, 3))
        self.assertEqual(cands[0].paire, ("surprise", "forte"))
        self.assertEqual(cands[0].repli, "aucun")

        # Rang 2
        self.assertEqual(cands[1].casier, (1, 3))
        self.assertEqual(cands[1].paire, ("surprise", "moyenne"))
        self.assertEqual(cands[1].repli, "intensite")

        # Rang 3
        self.assertEqual(cands[2].casier, (0, 3))
        self.assertEqual(cands[2].paire, ("surprise", "faible"))
        self.assertEqual(cands[2].repli, "intensite")

        # Rang 4 : tristesse / forte (sens horaire +1 avant sens antihoraire -1)
        self.assertEqual(cands[3].casier, (2, 4))
        self.assertEqual(cands[3].paire, ("tristesse", "forte"))
        self.assertEqual(cands[3].repli, "voisine_1")

        # Rang 5 : peur / forte (sens antihoraire -1)
        self.assertEqual(cands[4].casier, (2, 2))
        self.assertEqual(cands[4].paire, ("peur", "forte"))
        self.assertEqual(cands[4].repli, "voisine_1")

        # Suite distance 1 : moyenne puis faible
        self.assertEqual(cands[5].casier, (1, 4))  # tristesse / moyenne
        self.assertEqual(cands[6].casier, (1, 2))  # peur / moyenne
        self.assertEqual(cands[7].casier, (0, 4))  # tristesse / faible
        self.assertEqual(cands[8].casier, (0, 2))  # peur / faible

        # Distance 2 : degout (sens horaire +2) avant confiance (sens antihoraire -2)
        self.assertEqual(cands[9].casier, (2, 5))   # degout / forte
        self.assertEqual(cands[9].repli, "voisine_2")
        self.assertEqual(cands[10].casier, (2, 1))  # confiance / forte
        self.assertEqual(cands[10].repli, "voisine_2")
        self.assertEqual(cands[11].casier, (1, 5))  # degout / moyenne
        self.assertEqual(cands[12].casier, (1, 1))  # confiance / moyenne
        self.assertEqual(cands[13].casier, (0, 5))  # degout / faible
        self.assertEqual(cands[14].casier, (0, 1))  # confiance / faible

    def test_candidats_intensite_moyenne_departage(self):
        """Lorsque l'intensité cible est moyenne (rang 1), pour un même |Δintensity| = 1,
        la règle impose 'l'intensité la plus faible d'abord' (faible rang 0 avant forte rang 2).
        """
        cands = roue.candidats("joie", "moyenne")
        self.assertEqual(cands[0].paire, ("joie", "moyenne"))
        self.assertEqual(cands[0].repli, "aucun")
        # delta_i = 1 : faible (0) doit être avant forte (2)
        self.assertEqual(cands[1].paire, ("joie", "faible"))
        self.assertEqual(cands[1].repli, "intensite")
        self.assertEqual(cands[2].paire, ("joie", "forte"))
        self.assertEqual(cands[2].repli, "intensite")

    def test_repli_etiquettes(self):
        """Item 5 section 8 : vérifie la présence exacte des étiquettes de repli."""
        cands = roue.candidats("tristesse", "moyenne")
        replis = [c.repli for c in cands]
        self.assertEqual(replis.count("aucun"), 1)
        self.assertEqual(replis.count("intensite"), 2)
        self.assertEqual(replis.count("voisine_1"), 6)
        self.assertEqual(replis.count("voisine_2"), 6)


class TestSelecteur(unittest.TestCase):
    def test_bornes_lignes(self):
        # 'N' en ligne 0 est illégal
        self.assertFalse(selecteur.est_deplacement_valide((0, 4), "N"))
        with self.assertRaises(ValueError):
            selecteur.deplacer((0, 4), "N")

        # 'S' en ligne 2 est illégal
        self.assertFalse(selecteur.est_deplacement_valide((2, 4), "S"))
        with self.assertRaises(ValueError):
            selecteur.deplacer((2, 4), "S")

        # Mouvements verticaux permis
        self.assertEqual(selecteur.deplacer((1, 4), "N"), (0, 4))
        self.assertEqual(selecteur.deplacer((1, 4), "S"), (2, 4))

    def test_bouclage_colonnes_modulo_8(self):
        """Item 4 section 8 : déplacement du sélecteur et bouclage entre col 7 et col 0."""
        # 7 -> 0 par 'E'
        self.assertTrue(selecteur.est_deplacement_valide((1, 7), "E"))
        self.assertEqual(selecteur.deplacer((1, 7), "E"), (1, 0))

        # 0 -> 7 par 'O'
        self.assertTrue(selecteur.est_deplacement_valide((1, 0), "O"))
        self.assertEqual(selecteur.deplacer((1, 0), "O"), (1, 7))

    def test_exemples_annexe_c3(self):
        """Vérifie les 3 exemples chiffrés de l'annexe C.3."""
        # [1, 0] -> [1, 4] : horizontal a=4, 8-a=4 -> 4 x 'E', coût 4
        self.assertEqual(selecteur.distance((1, 0), (1, 4)), 4)
        self.assertEqual(selecteur.route((1, 0), (1, 4)), ["E", "E", "E", "E"])

        # [2, 7] -> [0, 1] : vertical 2 x 'N', horizontal 2 x 'E', coût 4
        self.assertEqual(selecteur.distance((2, 7), (0, 1)), 4)
        self.assertEqual(selecteur.route((2, 7), (0, 1), vertical_dabord=True), ["N", "N", "E", "E"])
        self.assertEqual(selecteur.route((2, 7), (0, 1), vertical_dabord=False), ["E", "E", "N", "N"])

        # [1, 0] -> [2, 6] : vertical 1 x 'S', horizontal a=6 -> 2 x 'O', coût 3 (l'exemple piège !)
        self.assertEqual(selecteur.distance((1, 0), (2, 6)), 3)
        self.assertEqual(selecteur.route((1, 0), (2, 6), vertical_dabord=True), ["S", "O", "O"])
        self.assertEqual(selecteur.route((1, 0), (2, 6), vertical_dabord=False), ["O", "O", "S"])

    def test_positions_traversees(self):
        """Vérifie le suivi des casiers visités selon annexe C.4."""
        # vertical d'abord : S, O, O depuis [1, 0] -> [2, 0], [2, 7], [2, 6]
        pos_v = selecteur.positions_traversees((1, 0), ["S", "O", "O"])
        self.assertEqual(pos_v, [(2, 0), (2, 7), (2, 6)])

        # horizontal d'abord : O, O, S depuis [1, 0] -> [1, 7], [1, 6], [2, 6]
        pos_h = selecteur.positions_traversees((1, 0), ["O", "O", "S"])
        self.assertEqual(pos_h, [(1, 7), (1, 6), (2, 6)])

    def test_classe_selecteur(self):
        sel = selecteur.Selecteur((1, 0))
        self.assertEqual(sel.casier, (1, 0))
        sel.avancer("S")
        self.assertEqual(sel.casier, (2, 0))
        sel.avancer("O")
        self.assertEqual(sel.casier, (2, 7))


# ---------------------------------------------------------------------------
# Tests CarteMentale — memoire.py
# ---------------------------------------------------------------------------

from robot import memoire as mem_module


class TestCarteMentale(unittest.TestCase):
    """Tests de la carte mentale (hypothèse optimiste + mise à jour)."""

    def _carte(self, **kwargs):
        """Crée une CarteMentale 7x7 avec les positions données."""
        return mem_module.CarteMentale(
            hauteur=kwargs.get("hauteur", 7),
            largeur=kwargs.get("largeur", 7),
            armoire=kwargs.get("armoire", (3, 5)),
            dictionnaire=kwargs.get("dictionnaire", (5, 3)),
            residents=kwargs.get("residents", [(1, 5)]),
        )

    def test_obstacles_connus_pre_remplis(self):
        """Armoire, dictionnaire et résidents sont non-traversables dès le début."""
        c = self._carte()
        self.assertFalse(c.est_traversable((3, 5)))   # armoire
        self.assertFalse(c.est_traversable((5, 3)))   # dictionnaire
        self.assertFalse(c.est_traversable((1, 5)))   # resident

    def test_case_inconnue_est_traversable(self):
        """Une case jamais vue est supposée libre (hypothèse optimiste)."""
        c = self._carte()
        self.assertTrue(c.est_traversable((2, 2)))   # jamais vue

    def test_hors_grille_non_traversable(self):
        """Une case hors des dimensions est toujours un mur virtuel."""
        c = self._carte()
        self.assertFalse(c.est_traversable((-1, 0)))
        self.assertFalse(c.est_traversable((0, 7)))
        self.assertFalse(c.est_traversable((7, 0)))

    def test_mettre_a_jour_revele_voisins(self):
        """mettre_a_jour() enregistre la position courante et les 4 voisins."""
        c = self._carte()
        perception = {"N": "mur", "S": "libre", "E": "libre", "O": "mur"}
        c.mettre_a_jour((3, 2), perception)

        # La case du robot est marquée libre
        self.assertTrue(c.est_traversable((3, 2)))
        self.assertEqual(c.type_case((3, 2)), "libre")

        # Voisins mis à jour
        self.assertFalse(c.est_traversable((2, 2)))   # N = mur
        self.assertTrue(c.est_traversable((4, 2)))    # S = libre
        self.assertTrue(c.est_traversable((3, 3)))    # E = libre
        self.assertFalse(c.est_traversable((3, 1)))   # O = mur

    def test_mur_decouvert_bloque_bfs(self):
        """Après avoir vu un mur, le BFS ne l'emprunte plus."""
        c = self._carte(hauteur=5, largeur=5, armoire=(0, 0),
                        dictionnaire=(0, 1), residents=[])
        depart = (1, 1)
        cible = {(1, 3)}

        # Sans mur intérieur : le chemin direct (1,1)→(1,2)→(1,3) est emprunté
        chemin_direct = chemin.plus_court_chemin(depart, cible, c.est_traversable)
        self.assertIsNotNone(chemin_direct)
        self.assertIn((1, 2), chemin_direct)

        # Découverte du mur en (1,2) → on met à jour la carte mentale
        c.cases[(1, 2)] = "mur"

        # Le BFS doit contourner sans passer par (1,2)
        chemin_apres = chemin.plus_court_chemin(depart, cible, c.est_traversable)
        self.assertIsNotNone(chemin_apres)
        self.assertNotIn((1, 2), chemin_apres)


# ---------------------------------------------------------------------------
# Tests BFS — chemin.py (items 1, 2, 7 de la section 8)
# ---------------------------------------------------------------------------

# Grille de l'annexe B.3 (6 colonnes x 5 lignes) :
#   colonne  0 1 2 3 4 5
#   ligne 0  # # # # # #
#   ligne 1  # R . # . #
#   ligne 2  # . # . . #
#   ligne 3  # . . . # #
#   ligne 4  # # # # # #
GRILLE_B3_MURS = {
    # bordure
    (0,0),(0,1),(0,2),(0,3),(0,4),(0,5),
    (4,0),(4,1),(4,2),(4,3),(4,4),(4,5),
    (1,0),(2,0),(3,0),
    (1,5),(2,5),(3,5),
    # murs interieurs
    (1,3),(2,2),(3,4),
}


def _traversable_b3(pos):
    return pos not in GRILLE_B3_MURS


class TestChemin(unittest.TestCase):
    """Item 1 section 8 : planification sur une petite grille de longueur connue."""

    def test_chemin_longueur_connue_annexe_b3(self):
        """Chemin de (1,1) a (1,4) sur la grille de l'annexe B.3.

        Seul itineraire : (1,1)->(2,1)->(3,1)->(3,2)->(3,3)->(2,3)->(2,4)->(1,4)
        7 pas = 8 cases dont depart et arrivee.
        """
        resultat = chemin.plus_court_chemin((1, 1), {(1, 4)}, _traversable_b3)
        self.assertIsNotNone(resultat, "Un chemin doit exister")
        self.assertEqual(resultat[0], (1, 1))
        self.assertEqual(resultat[-1], (1, 4))
        self.assertEqual(len(resultat), 8)

    def test_premier_pas(self):
        """premier_pas() renvoie la case immediatement suivante."""
        pas = chemin.premier_pas((1, 1), {(1, 4)}, _traversable_b3)
        self.assertEqual(pas, (2, 1))

    def test_cible_deja_atteinte(self):
        """Si le depart est la cible, chemin=[depart] et premier_pas=None."""
        resultat = chemin.plus_court_chemin((1, 1), {(1, 1)}, _traversable_b3)
        self.assertEqual(resultat, [(1, 1)])
        self.assertIsNone(chemin.premier_pas((1, 1), {(1, 1)}, _traversable_b3))

    def test_multi_cibles(self):
        """Avec plusieurs cibles, le BFS trouve la plus proche."""
        # (2,1) est a 1 pas, (1,4) est a 7 pas
        resultat = chemin.plus_court_chemin((1, 1), {(2, 1), (1, 4)}, _traversable_b3)
        self.assertIsNotNone(resultat)
        self.assertEqual(len(resultat), 2)
        self.assertEqual(resultat[-1], (2, 1))


class TestReplanification(unittest.TestCase):
    """Item 2 section 8 : replanification apres decouverte d'un mur."""

    @staticmethod
    def _traversable_sans_mur(pos):
        l, c = pos
        return 0 < l < 4 and 0 < c < 4  # grille 5x5, bordure = mur

    @staticmethod
    def _traversable_avec_mur_1_2(pos):
        if pos == (1, 2):
            return False  # mur decouvert en (1,2)
        l, c = pos
        return 0 < l < 4 and 0 < c < 4

    def test_chemin_initial_direct(self):
        """Sans mur interieur, le chemin direct (1,1)->(1,2)->(1,3) fait 2 pas."""
        resultat = chemin.plus_court_chemin(
            (1, 1), {(1, 3)}, self._traversable_sans_mur
        )
        self.assertIsNotNone(resultat)
        self.assertEqual(len(resultat), 3)

    def test_replanification_apres_mur(self):
        """Apres decouverte du mur en (1,2), le chemin s'allonge et l'evite."""
        resultat = chemin.plus_court_chemin(
            (1, 1), {(1, 3)}, self._traversable_avec_mur_1_2
        )
        self.assertIsNotNone(resultat, "Un contournement doit exister")
        self.assertNotIn((1, 2), resultat)
        self.assertGreater(len(resultat), 3)
        self.assertEqual(resultat[0], (1, 1))
        self.assertEqual(resultat[-1], (1, 3))


class TestResidentInaccessible(unittest.TestCase):
    """Item 7 section 8 : resident mure sur une grille miniature."""

    # Grille 5x5 :
    #   # # # # #
    #   # R # P #    cloison verticale complete en colonne 2 (lignes 1,2,3)
    #   # . # . #
    #   # . # . #
    #   # # # # #
    # Le cote gauche (robot) et le cote droit (resident P en (1,3)) sont
    # completement separes : aucun chemin possible.
    MURS = {
        (0,0),(0,1),(0,2),(0,3),(0,4),
        (4,0),(4,1),(4,2),(4,3),(4,4),
        (1,0),(2,0),(3,0),
        (1,4),(2,4),(3,4),
        # cloison complete : col 2 sur toutes les lignes interieures
        (1,2),(2,2),(3,2),
    }
    # P est en (1,3) — isole a droite de la cloison

    @classmethod
    def _traversable(cls, pos):
        return pos not in cls.MURS

    def test_resident_inaccessible(self):
        """BFS renvoie None -> preuve d'inaccessibilite (annexe B.6)."""
        # Voisins libres de P(1,3) : (2,3) uniquement (les autres sont murs)
        resultat = chemin.plus_court_chemin((1, 1), {(2, 3)}, self._traversable)
        self.assertIsNone(resultat)

    def test_cases_adjacentes_libres_helper(self):
        """cases_adjacentes_libres() construit l'ensemble des cibles correctement."""
        libres = chemin.cases_adjacentes_libres((1, 3), self._traversable)
        # voisins de (1,3) : (0,3)=mur, (1,2)=mur, (1,4)=mur, (2,3)=libre
        self.assertEqual(libres, {(2, 3)})


if __name__ == "__main__":
    unittest.main()
