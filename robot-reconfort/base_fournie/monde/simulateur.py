# monde/simulateur.py
# 
# C'est LE SEUL fichier qui a le droit de lire `grille` et `objet`.
# Le robot n'y touche jamais directement.
#
# Le simulateur connait la vraie carte et la vraie armoire.
# Le robot lui envoie des actions, le simulateur repond avec des perceptions.

from robot import geometrie

# traduction symbole carte -> mot perception
SYMBOLE_VERS_TYPE = {
    "#": "mur",
    ".": "libre",
    "R": "libre",   # case de depart = case libre
    "A": "armoire",
    "D": "dictionnaire",
    "P": "resident",
}


class Simulateur:
    """Gere l'etat reel du monde : position du robot, contenu de l'armoire, etc."""

    def __init__(self, carte, armoire):
        """
        carte   : dict charge depuis carte.json   (via charger_carte)
        armoire : dict charge depuis armoire.json  (via charger_armoire)
        """
        # la vraie grille (liste de strings)
        self.grille = carte["grille"]
        self.hauteur = carte["dimensions"]["hauteur"]
        self.largeur = carte["dimensions"]["largeur"]

        # position du robot (peut changer a chaque AVANCER)
        self.position = tuple(carte["depart_robot"])

        # positions des elements fixes
        self.pos_armoire = tuple(carte["armoire"]["position"])
        self.pos_dictionnaire = tuple(carte["dictionnaire"]["position"])
        # dict id -> position pour les residents
        self.residents = {
            r["id"]: tuple(r["position"])
            for r in carte["residents"]
        }

        # contenu reel de l'armoire : {(ligne, col) -> nom_objet ou None}
        self.contenu_armoire = {}
        for casier in armoire["casiers"]:
            pos = (casier["ligne"], casier["colonne"])
            self.contenu_armoire[pos] = casier["objet"]  # None si vide

        # position du selecteur dans l'armoire
        self.selecteur = tuple(armoire["casier_depart"])

        # objet que le robot transporte (None si les mains sont vides)
        self.objet_porte = None

    # ------------------------------------------------------------------
    # Perception
    # ------------------------------------------------------------------

    def percevoir(self):
        """Renvoie ce que le robot voit autour de lui (les 4 cases adjacentes)."""
        perception = {}
        for direction in geometrie.DIRECTIONS:
            voisin = geometrie.deplacer(self.position, direction)
            perception[direction] = self._type_case(voisin)
        return perception

    def contenu_casier_courant(self):
        """Renvoie le contenu du casier ou se trouve le selecteur.
        
        Seulement si le robot est adjacent a l'armoire, sinon None.
        """
        if self._adjacent_a(self.pos_armoire):
            return self.contenu_armoire.get(self.selecteur)
        return None

    # ------------------------------------------------------------------
    # Application des actions
    # ------------------------------------------------------------------

    def appliquer(self, action, argument=None):
        """Execute une action et met a jour l'etat du monde.
        
        Leve une ValueError si l'action est illegale (utilise en tests).
        """
        if action == "AVANCER":
            self._avancer(argument)
        elif action == "CONSULTER":
            self._consulter()
        elif action == "CHERCHER":
            self._chercher(argument)
        elif action == "PRENDRE":
            self._prendre(argument)
        elif action == "DONNER":
            self._donner(argument)
        elif action == "ATTENDRE":
            pass  # rien a faire
        else:
            raise ValueError(f"Action inconnue : {action}")

    def _avancer(self, direction):
        cible = geometrie.deplacer(self.position, direction)
        if self._type_case(cible) != "libre":
            raise ValueError(f"AVANCER {direction} : case {cible} non libre ({self._type_case(cible)})")
        self.position = cible

    def _consulter(self):
        if not self._adjacent_a(self.pos_dictionnaire):
            raise ValueError("CONSULTER : robot pas adjacent au dictionnaire")
        # rien a faire dans le simulateur, c'est le robot qui traite le message

    def _chercher(self, direction):
        if not self._adjacent_a(self.pos_armoire):
            raise ValueError("CHERCHER : robot pas adjacent a l'armoire")
        l, c = self.selecteur
        if direction == "N":
            if l <= 0:
                raise ValueError("CHERCHER N : deja en ligne 0")
            self.selecteur = (l - 1, c)
        elif direction == "S":
            if l >= 2:
                raise ValueError("CHERCHER S : deja en ligne 2")
            self.selecteur = (l + 1, c)
        elif direction == "E":
            self.selecteur = (l, (c + 1) % 8)
        elif direction == "O":
            self.selecteur = (l, (c - 1) % 8)
        else:
            raise ValueError(f"CHERCHER : direction inconnue {direction}")

    def _prendre(self, nom_objet):
        if not self._adjacent_a(self.pos_armoire):
            raise ValueError("PRENDRE : robot pas adjacent a l'armoire")
        if self.objet_porte is not None:
            raise ValueError(f"PRENDRE : robot porte deja {self.objet_porte}")
        contenu = self.contenu_armoire.get(self.selecteur)
        if contenu is None:
            raise ValueError(f"PRENDRE : casier {self.selecteur} est vide")
        if contenu != nom_objet:
            raise ValueError(f"PRENDRE : casier contient {contenu!r}, pas {nom_objet!r}")
        self.objet_porte = contenu
        # en projet 1 on ne vide pas le casier (le stock est infini)

    def _donner(self, nom_objet):
        # trouver le resident adjacent
        resident_id = self._resident_adjacent()
        if resident_id is None:
            raise ValueError("DONNER : aucun resident adjacent")
        if self.objet_porte != nom_objet:
            raise ValueError(f"DONNER : robot porte {self.objet_porte!r}, pas {nom_objet!r}")
        self.objet_porte = None

    # ------------------------------------------------------------------
    # Utilitaires internes
    # ------------------------------------------------------------------

    def _type_case(self, pos):
        """Lit le symbole dans la vraie grille et le convertit en mot."""
        l, c = pos
        if not (0 <= l < self.hauteur and 0 <= c < self.largeur):
            return "mur"
        symbole = self.grille[l][c]
        return SYMBOLE_VERS_TYPE.get(symbole, "mur")

    def _adjacent_a(self, cible):
        """Verifie si le robot est sur une case orthogonalement adjacente a cible."""
        l, c = self.position
        tl, tc = cible
        return abs(l - tl) + abs(c - tc) == 1

    def _resident_adjacent(self):
        """Retourne l'id du resident adjacent, ou None."""
        for rid, pos in self.residents.items():
            if self._adjacent_a(pos):
                return rid
        return None
