# robot/decision.py
# Machine a etats du robot pour une demande.
#
# Ordre des etats par demande (section 4 de l'enonce) :
#   ALLER_DICTIONNAIRE -> CONSULTER -> ALLER_ARMOIRE -> FOUILLER -> PRENDRE
#   -> ALLER_RESIDENT -> DONNER -> DONE
#
# En cas d'echec : etat = ECHEC, motif_echec = "emotion indeterminee" |
#                                               "armoire vide" |
#                                               "resident inaccessible"

from robot import chemin, geometrie, roue
from robot import selecteur as sel_module


class Robot:

    def __init__(self, carte, lecteur, pos_armoire, pos_dictionnaire, residents):
        """
        carte            : CarteMentale
        lecteur          : LecteurEmotion (deja charge)
        pos_armoire      : tuple (l, c)
        pos_dictionnaire : tuple (l, c)
        residents        : dict {id -> (l, c)}
        """
        self.carte    = carte
        self.lecteur  = lecteur
        self.pos_arm  = pos_armoire
        self.pos_dico = pos_dictionnaire
        self.residents = residents

        # ce qu'on a deja vu dans l'armoire : {(l,c) -> objet ou None}
        # persiste entre les demandes (section 4 : l'etat persiste)
        self.casiers_vus = {}

        # champs de la demande en cours (reinitialises par nouvelle_demande)
        self.etat         = "RIEN"
        self.message      = None
        self.resident_id  = None
        self.emotion      = None
        self.intensite    = None
        self.candidats    = []
        self.objet_porte  = None   # conserve jusqu'a la prochaine demande pour la trace
        self.casier_choisi = None
        self.repli        = "aucun"
        self.motif_echec  = None

    # ------------------------------------------------------------------
    # Interface appelee par agent.py
    # ------------------------------------------------------------------

    def nouvelle_demande(self, message, resident_id):
        """Reinitialise l'etat pour une nouvelle demande."""
        self.message      = message
        self.resident_id  = resident_id
        self.emotion      = None
        self.intensite    = None
        self.candidats    = []
        self.objet_porte  = None
        self.casier_choisi = None
        self.repli        = "aucun"
        self.motif_echec  = None
        self.etat         = "ALLER_DICTIONNAIRE"

    def mettre_a_jour(self, position, perception, sel_pos, contenu):
        """Met a jour la carte mentale et la memoire de l'armoire."""
        self.carte.mettre_a_jour(position, perception)
        # si on est adjacent a l'armoire, on enregistre le contenu du casier courant
        if self._adjacent(position, self.pos_arm):
            self.casiers_vus[sel_pos] = contenu  # None = casier vide

    def decider(self, position, sel_pos):
        """Retourne (action, argument) pour ce tick.
        
        On boucle jusqu'a 10 fois pour permettre des transitions d'etat
        sans action (ex: on arrive pres du dico et on consulte tout de suite).
        """
        for _ in range(10):
            result = self._step(position, sel_pos)
            if result is not None:
                return result
        return ("ATTENDRE", None)  # securite

    @property
    def est_termine(self):
        return self.etat in ("DONE", "ECHEC")

    @property
    def est_succes(self):
        return self.etat == "DONE"

    # ------------------------------------------------------------------
    # Machine a etats
    # ------------------------------------------------------------------

    def _step(self, position, sel_pos):
        """Un pas de la machine. Retourne une action ou None (transition pure)."""

        if self.etat == "ALLER_DICTIONNAIRE":
            cibles = chemin.cases_adjacentes_libres(self.pos_dico, self.carte.est_traversable)
            if position in cibles:
                self.etat = "CONSULTER"
                return None  # transition immediate -> prochain _step
            return self._avancer(position, cibles, "resident inaccessible")

        elif self.etat == "CONSULTER":
            res = self.lecteur.identifier(self.message)
            if res is None:
                self.etat        = "ECHEC"
                self.motif_echec = "emotion indeterminee"
                return ("ATTENDRE", None)
            self.emotion, self.intensite = res
            self.candidats = roue.candidats(self.emotion, self.intensite)
            self.etat = "ALLER_ARMOIRE"
            return ("CONSULTER", None)

        elif self.etat == "ALLER_ARMOIRE":
            cibles = chemin.cases_adjacentes_libres(self.pos_arm, self.carte.est_traversable)
            if position in cibles:
                self.etat = "FOUILLER"
                return None
            return self._avancer(position, cibles, "resident inaccessible")

        elif self.etat == "FOUILLER":
            return self._fouiller(sel_pos)

        elif self.etat == "PRENDRE":
            action = ("PRENDRE", self.objet_porte)
            self.etat = "ALLER_RESIDENT"
            return action

        elif self.etat == "ALLER_RESIDENT":
            pos_res = self.residents[self.resident_id]
            cibles  = chemin.cases_adjacentes_libres(pos_res, self.carte.est_traversable)
            if position in cibles:
                self.etat = "DONNER"
                return None
            return self._avancer(position, cibles, "resident inaccessible")

        elif self.etat == "DONNER":
            action = ("DONNER", self.objet_porte)
            self.etat = "DONE"
            return action

        # DONE / ECHEC : ne devrait plus etre appele
        return ("ATTENDRE", None)

    # ------------------------------------------------------------------
    # Logique de fouille de l'armoire
    # ------------------------------------------------------------------

    def _fouiller(self, sel_pos):
        """Choisit le prochain mouvement dans l'armoire.
        
        On cherche le premier candidat non connu comme vide.
        Si on est dessus -> PRENDRE. Sinon -> CHERCHER un pas vers lui.
        """
        cible = None
        for cand in self.candidats:
            casier = cand.casier
            if casier not in self.casiers_vus:
                cible = cand; break  # jamais vu : peut etre garni
            if self.casiers_vus[casier] is not None:
                cible = cand; break  # connu comme garni
            # connu vide -> on passe au suivant

        if cible is None:
            self.etat        = "ECHEC"
            self.motif_echec = "armoire vide"
            return ("ATTENDRE", None)

        if sel_pos == cible.casier:
            # on est la, le contenu a ete enregistre par mettre_a_jour ce tick
            self.objet_porte   = self.casiers_vus[cible.casier]
            self.casier_choisi = cible.casier
            self.repli         = cible.repli
            self.etat          = "PRENDRE"
            return None  # transition immediate

        # on n'est pas encore au bon casier : un pas vers lui
        mouvements = sel_module.route(sel_pos, cible.casier)
        return ("CHERCHER", mouvements[0])

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _avancer(self, position, cibles, motif_si_impossible):
        """Renvoie AVANCER vers cibles, ou ECHEC si le BFS ne trouve rien."""
        if not cibles:
            self.etat        = "ECHEC"
            self.motif_echec = motif_si_impossible
            return ("ATTENDRE", None)
        prochain = chemin.premier_pas(position, cibles, self.carte.est_traversable)
        if prochain is None:
            self.etat        = "ECHEC"
            self.motif_echec = motif_si_impossible
            return ("ATTENDRE", None)
        direction = geometrie.direction_entre(position, prochain)
        return ("AVANCER", direction)

    @staticmethod
    def _adjacent(pos, cible):
        """Verifie si pos est orthogonalement adjacent a cible."""
        return abs(pos[0] - cible[0]) + abs(pos[1] - cible[1]) == 1
