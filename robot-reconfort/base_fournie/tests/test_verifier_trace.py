"""
tests/test_verifier_trace.py — Tests pour le verificateur de trace (Phase 8).
"""

import copy
import json
import unittest
from pathlib import Path

DOSSIER_BASE = Path(__file__).resolve().parent.parent
from outils.verifier_trace import verifier_trace, ErreurTrace


class TestVerifierTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DOSSIER_BASE / "cartes" / "appartement_01.json", "r", encoding="utf-8") as f:
            cls.carte = json.load(f)
        with open(DOSSIER_BASE / "cartes" / "scenario_01.json", "r", encoding="utf-8") as f:
            cls.scenario = json.load(f)
        with open(DOSSIER_BASE / "donnees" / "armoire_standard.json", "r", encoding="utf-8") as f:
            cls.armoire = json.load(f)
        with open(DOSSIER_BASE / "sorties" / "trace_01.json", "r", encoding="utf-8") as f:
            cls.trace_valide = json.load(f)

    def test_trace_valide_passe(self):
        """Une trace valide doit passer sans lever d'exception."""
        res = verifier_trace(self.carte, self.scenario, self.armoire, self.trace_valide)
        self.assertTrue(res)

    def test_perception_falsifiee_rejetee(self):
        """Une perception ne correspondant pas a la realite doit etre rejetee."""
        trace = copy.deepcopy(self.trace_valide)
        # On ment sur la perception au pas 0 (on dit qu'il y a un mur au Nord alors que c'est libre)
        trace["pas"][0]["perception"]["N"] = "mur"
        with self.assertRaises(ErreurTrace) as ctx:
            verifier_trace(self.carte, self.scenario, self.armoire, trace)
        self.assertIn("perception falsifiee", str(ctx.exception).lower())

    def test_mouvement_illegal_rejete(self):
        """Un deplacement vers un mur doit etre rejete."""
        trace = copy.deepcopy(self.trace_valide)
        # Au pas 0, le robot avance vers l'Ouest (dans le mur exterieur)
        trace["pas"][0]["argument"] = "O"
        with self.assertRaises(ErreurTrace) as ctx:
            verifier_trace(self.carte, self.scenario, self.armoire, trace)
        self.assertIn("non traversable", str(ctx.exception).lower())

    def test_contenu_casier_falsifie_rejete(self):
        """Un contenu_casier non null loin de l'armoire doit etre rejete."""
        trace = copy.deepcopy(self.trace_valide)
        # Au pas 0 (le robot est en [6, 1], non adjacent a l'armoire en [6, 4])
        trace["pas"][0]["contenu_casier"] = "tisane"
        with self.assertRaises(ErreurTrace) as ctx:
            verifier_trace(self.carte, self.scenario, self.armoire, trace)
        self.assertIn("null", str(ctx.exception).lower())

    def test_resume_incoherent_rejete(self):
        """Un resume dont le total de pas est faux doit etre rejete."""
        trace = copy.deepcopy(self.trace_valide)
        trace["resume"]["pas_total"] = 999
        with self.assertRaises(ErreurTrace) as ctx:
            verifier_trace(self.carte, self.scenario, self.armoire, trace)
        self.assertIn("pas_total", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
