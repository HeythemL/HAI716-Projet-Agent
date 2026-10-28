from robot import geometrie

# types qui bloquent le passage du robot
OBSTACLES = {"mur", "armoire", "dictionnaire", "resident"}


class CarteMentale:
    """La carte que le robot construit lui-meme au fur et a mesure.
    
    Au depart il ne connait rien (sauf l'armoire, le dico et les residents
    dont les positions sont donnees dans le fichier carte).
    Tout ce qu'il n'a pas encore vu est suppose libre (hypothese optimiste).
    """

    def __init__(self, hauteur, largeur, armoire, dictionnaire, residents):
        self.hauteur = hauteur
        self.largeur = largeur

        # cases connues : {(ligne, col) -> "libre" | "mur" | "armoire" | ...}
        # si une case n'est pas dans ce dict, on suppose qu'elle est libre
        self.cases = {}

        # on sait deja que ces positions sont des obstacles (enonce section 3.2)
        self.cases[tuple(armoire)] = "armoire"
        self.cases[tuple(dictionnaire)] = "dictionnaire"
        for pos in residents:
            self.cases[tuple(pos)] = "resident"

    def mettre_a_jour(self, position, perception):
        """Appele a chaque tick avec ce que le robot voit autour de lui.
        
        position  : ou est le robot maintenant
        perception: {"N": "mur", "S": "libre", ...} les 4 cases adjacentes
        """
        # le robot est la, donc cette case est libre
        self.cases[position] = "libre"

        # on note le type de chacun des 4 voisins
        for direction, type_case in perception.items():
            voisin = geometrie.deplacer(position, direction)
            self.cases[voisin] = type_case

    def est_traversable(self, case):
        """Est-ce que le robot peut aller sur cette case ?
        
        - hors de la grille     -> non
        - obstacle connu        -> non
        - jamais vu (inconnu)   -> oui (on suppose libre, on verra bien)
        - libre                 -> oui
        """
        l, c = case
        # en dehors des murs de la grille
        if not (0 <= l < self.hauteur and 0 <= c < self.largeur):
            return False

        type_case = self.cases.get(case)  # None si on n'a jamais vu cette case
        if type_case is None:
            return True  # inconnu = suppose libre
        return type_case not in OBSTACLES

    def type_case(self, case):
        """Retourne ce qu'on sait de cette case, ou None si jamais vue."""
        return self.cases.get(case)
