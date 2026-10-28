EMOTIONS_DEFAUT = (
    "joie",
    "confiance",
    "peur",
    "surprise",
    "tristesse",
    "degout",
    "colere",
    "anticipation",
)

INTENSITES_DEFAUT = (
    "faible",
    "moyenne",
    "forte",
)

REPLI_AUCUN = "aucun"
REPLI_INTENSITE = "intensite"
REPLI_VOISINE_1 = "voisine_1"
REPLI_VOISINE_2 = "voisine_2"


def distance(e1, e2, emotions=EMOTIONS_DEFAUT):
    """Calcule la distance sur la roue de Plutchik entre deux emotions."""
    i1 = emotions.index(e1)
    i2 = emotions.index(e2)
    k = (i2 - i1) % 8
    return min(k, 8 - k)


class Candidat:
    """Represente un casier candidat avec ses informations."""

    def __init__(self, emotion, intensite, repli, ligne, colonne):
        self.emotion = emotion
        self.intensite = intensite
        self.repli = repli
        self.ligne = ligne
        self.colonne = colonne
        self.casier = (ligne, colonne)
        self.paire = (emotion, intensite)

    def __iter__(self):
        return iter((self.emotion, self.intensite, self.repli))

    def __getitem__(self, index):
        return (self.emotion, self.intensite, self.repli)[index]

    def __len__(self):
        return 3

    def __repr__(self):
        return f"Candidat({self.emotion}, {self.intensite}, repli={self.repli}, casier={self.casier})"

    def __eq__(self, other):
        if isinstance(other, Candidat):
            return (self.emotion, self.intensite, self.repli, self.ligne, self.colonne) == (
                other.emotion, other.intensite, other.repli, other.ligne, other.colonne
            )
        if isinstance(other, tuple):
            if len(other) == 2:
                return (self.emotion, self.intensite) == other
            if len(other) == 3:
                return (self.emotion, self.intensite, self.repli) == other
        return False


def determiner_repli(dist, delta_i):
    """Determine l'etiquette de repli selon la distance et l'intensite."""
    if dist == 0:
        if delta_i == 0:
            return REPLI_AUCUN
        return REPLI_INTENSITE
    elif dist == 1:
        return REPLI_VOISINE_1
    elif dist == 2:
        return REPLI_VOISINE_2
    raise ValueError("Distance impossible : " + str(dist))


def candidats(e, i, emotions=EMOTIONS_DEFAUT, intensites=INTENSITES_DEFAUT):
    """Calcule la liste ordonnee des 15 casiers candidats."""
    idx_target = emotions.index(e)
    r_target = intensites.index(i)

    liste = []
    for col_idx in range(len(emotions)):
        e_cand = emotions[col_idx]

        # Distance sur la roue
        k = (col_idx - idx_target) % 8
        dist = min(k, 8 - k)
        if dist > 2:
            continue

        # Sens horaire (+dist) avant anti-horaire (-dist)
        if dist == 0:
            sens_flag = 0
        else:
            est_horaire = ((idx_target + dist) % 8 == col_idx)
            sens_flag = 0 if est_horaire else 1

        for row_idx in range(len(intensites)):
            i_cand = intensites[row_idx]
            delta_i = abs(row_idx - r_target)
            repli = determiner_repli(dist, delta_i)

            candidat = Candidat(e_cand, i_cand, repli, row_idx, col_idx)
            # Tri selon : distance, ecart intensite, intensite la plus faible, sens horaire
            cle = (dist, delta_i, row_idx, sens_flag)
            liste.append((cle, candidat))

    liste.sort(key=lambda x: x[0])

    resultat = []
    for cle, cand in liste:
        resultat.append(cand)
    return resultat
