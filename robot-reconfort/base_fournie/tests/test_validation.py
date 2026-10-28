"""
test_validation.py — Tests unitaires et tests subprocess pour la validation (Phase 6).

Verifie l'ensemble des cas d'erreur de la section 5.6 :
  1. Fichier absent
  2. Fichier non encode en UTF-8
  3. JSON invalide
  4. Format inattendu
  5. Version inattendue
  6. Champ obligatoire manquant
  7. Champ avec type invalide
  8. Grille non rectangulaire
  9. Dimensions de grille incoherentes
  10. Position hors grille
  11. Symbole depart robot incoherent
  12. Symbole armoire incoherent
  13. Symbole dictionnaire incoherent
  14. Symbole resident incoherent
  15. Deux residents avec le meme identifiant
  16. Scenario prevu pour une autre carte
  17. Demande adressee a un resident absent de la carte
  18. Armoire absente du dossier de donnees
  19. Casier_depart hors de l'armoire
  20. Casier hors des dimensions de l'armoire
  21. Casier en double dans l'armoire
  22. Etiquette casier incoherente avec sa position
  23. Dictionnaire avec emotion inconnue
  24. Dictionnaire avec intensite inconnue
  25. Dictionnaire avec un mot dans deux entrees differentes
  26. Nombre d'arguments invalide sur agent.py (exit code 2)
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

# Ajouter base_fournie au sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from reconfort_io import ErreurFichier, charger_carte, charger_scenario, charger_armoire, charger_dictionnaire
from validation import (
    valider_carte,
    valider_scenario,
    valider_armoire,
    valider_dictionnaire,
    valider_coherence,
    valider_tout,
)


class TestValidationUnitaire(unittest.TestCase):
    """Verifications directes des fonctions du module validation.py."""

    @classmethod
    def setUpClass(cls):
        cls.carte_valide = charger_carte(BASE_DIR / "cartes" / "appartement_01.json")
        cls.scenario_valide = charger_scenario(BASE_DIR / "cartes" / "scenario_01.json")
        cls.armoire_valide = charger_armoire(BASE_DIR / "donnees" / "armoire_standard.json")
        cls.dico_valide = charger_dictionnaire(BASE_DIR / "donnees" / "dictionnaire.json")

    def test_fichiers_valides_passent(self):
        """Les fichiers fournis doivent tous etre valides sans lever d'exception."""
        valider_carte(self.carte_valide)
        valider_scenario(self.scenario_valide)
        valider_armoire(self.armoire_valide)
        valider_dictionnaire(self.dico_valide)
        valider_coherence(self.carte_valide, self.scenario_valide, self.armoire_valide, self.dico_valide)

    def test_valider_tout_succes(self):
        """valider_tout doit charger et valider les fichiers sans erreur."""
        c, s, a, d = valider_tout(
            BASE_DIR / "cartes" / "appartement_01.json",
            BASE_DIR / "cartes" / "scenario_01.json",
            BASE_DIR / "donnees",
        )
        self.assertEqual(c["nom"], "appartement_01")
        self.assertEqual(s["nom"], "scenario_01")
        self.assertEqual(a["nom"], "armoire_standard")
        self.assertEqual(d["nom"], "dictionnaire_residence")

    def test_dossier_donnees_introuvable(self):
        """Un dossier de donnees inexistant doit lever ErreurFichier."""
        with self.assertRaises(ErreurFichier):
            valider_tout(
                BASE_DIR / "cartes" / "appartement_01.json",
                BASE_DIR / "cartes" / "scenario_01.json",
                BASE_DIR / "dossier_fantome",
            )


class TestValidationSubprocess(unittest.TestCase):
    """Verifie le contrat d'appel d'agent.py en sous-processus sur tous les fichiers casses.

    Pour chaque fichier casse :
      1. Code de retour non nul (sys.exit(1) ou sys.exit(2))
      2. Message explicite sur stderr
      3. Pas de trace d'exception (Traceback) sur stderr
      4. Aucun fichier de trace cree
    """

    @classmethod
    def setUpClass(cls):
        cls.agent_py = BASE_DIR / "agent.py"
        cls.casses_dir = BASE_DIR / "tests" / "fichiers_casses"
        cls.carte_normale = BASE_DIR / "cartes" / "appartement_01.json"
        cls.scenario_normal = BASE_DIR / "cartes" / "scenario_01.json"
        cls.donnees_normales = BASE_DIR / "donnees"
        cls.trace_temp = BASE_DIR / "tests" / "trace_test_invalide.json"

    def tearDown(self):
        if self.trace_temp.exists():
            try:
                self.trace_temp.unlink()
            except OSError:
                pass

    def _executer_agent(self, carte, scenario, donnees):
        """Execute agent.py avec les arguments donnes et capture code/stdout/stderr."""
        if self.trace_temp.exists():
            self.trace_temp.unlink()

        res = subprocess.run(
            [
                sys.executable,
                str(self.agent_py),
                str(carte),
                str(scenario),
                str(donnees),
                str(self.trace_temp),
            ],
            capture_output=True,
            text=True,
        )

        # Assertions communes a tous les fichiers casses
        self.assertNotEqual(
            res.returncode,
            0,
            f"agent.py aurait du echouer avec un code non nul (code={res.returncode})",
        )
        self.assertTrue(
            len(res.stderr.strip()) > 0,
            "Un message explicatif doit etre ecrit sur stderr",
        )
        self.assertNotIn(
            "Traceback (most recent call last):",
            res.stderr,
            f"Aucune trace d'exception (traceback) ne doit apparaitre sur stderr:\n{res.stderr}",
        )
        self.assertFalse(
            self.trace_temp.exists(),
            "Aucun fichier de trace ne doit etre ecrit en cas d'erreur de validation",
        )
        return res

    def test_01_fichier_absent(self):
        """Fichier absent -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "carte_inexistante.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("fichier introuvable", res.stderr.lower())

    def test_02_fichier_non_utf8(self):
        """Fichier non encode en UTF-8 -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "02_non_utf8.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("utf-8", res.stderr.lower())

    def test_03_json_invalide(self):
        """Fichier JSON malforme -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "03_json_invalide.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("json", res.stderr.lower())

    def test_04_format_inattendu(self):
        """Format inattendu -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "04_format_inattendu.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("format attendu", res.stderr.lower())

    def test_05_version_inattendue(self):
        """Version inattendue -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "05_version_inattendue.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("version", res.stderr.lower())

    def test_06_carte_champ_manquant(self):
        """Champ obligatoire manquant dans la carte -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "06_carte_champ_manquant.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("champ obligatoire manquant", res.stderr.lower())

    def test_07_carte_type_invalide(self):
        """Champ de type invalide dans la carte -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "07_carte_type_invalide.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("doit etre de type", res.stderr.lower())

    def test_08_carte_grille_non_rectangulaire(self):
        """Grille non rectangulaire -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "08_carte_grille_non_rectangulaire.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("grille non rectangulaire", res.stderr.lower())

    def test_09_carte_dimensions_incoherentes(self):
        """Dimensions annoncees incoherentes -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "09_carte_dimensions_incoherentes.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("dimensions", res.stderr.lower())

    def test_10_carte_position_hors_grille(self):
        """Position hors grille -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "10_carte_position_hors_grille.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("hors de la grille", res.stderr.lower())

    def test_11_carte_symbole_robot_incoherent(self):
        """Symbole robot non 'R' sur la grille -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "11_carte_symbole_robot_incoherent.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("symbole", res.stderr.lower())

    def test_12_carte_symbole_armoire_incoherent(self):
        """Symbole armoire non 'A' sur la grille -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "12_carte_symbole_armoire_incoherent.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("symbole", res.stderr.lower())

    def test_13_carte_symbole_dico_incoherent(self):
        """Symbole dictionnaire non 'D' sur la grille -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "13_carte_symbole_dico_incoherent.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("symbole", res.stderr.lower())

    def test_14_carte_symbole_resident_incoherent(self):
        """Symbole resident non 'P' sur la grille -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "14_carte_symbole_resident_incoherent.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("symbole", res.stderr.lower())

    def test_15_carte_resident_doublon_id(self):
        """Deux residents avec le meme identifiant -> echec propre."""
        res = self._executer_agent(
            self.casses_dir / "15_carte_resident_doublon_id.json",
            self.scenario_normal,
            self.donnees_normales,
        )
        self.assertIn("meme identifiant", res.stderr.lower())

    def test_16_scenario_carte_incoherente(self):
        """Scenario prevu pour une autre carte -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.casses_dir / "16_scenario_carte_incoherente.json",
            self.donnees_normales,
        )
        self.assertIn("incoherence", res.stderr.lower())

    def test_17_scenario_resident_inconnu(self):
        """Demande adressee a un resident absent de la carte -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.casses_dir / "17_scenario_resident_inconnu.json",
            self.donnees_normales,
        )
        self.assertIn("resident inconnu", res.stderr.lower())

    def test_18_scenario_armoire_absente(self):
        """Armoire specifiee par le scenario absente des donnees -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.casses_dir / "18_scenario_armoire_absente.json",
            self.donnees_normales,
        )
        self.assertIn("fichier introuvable", res.stderr.lower())

    def test_19_armoire_casier_depart_hors_bornes(self):
        """casier_depart hors de l'armoire -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.scenario_normal,
            self.casses_dir / "donnees_armoire_depart_hors_bornes",
        )
        self.assertIn("casier_depart hors de l'armoire", res.stderr.lower())

    def test_20_armoire_casier_hors_bornes(self):
        """Casier hors des dimensions de l'armoire -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.scenario_normal,
            self.casses_dir / "donnees_armoire_casier_hors_bornes",
        )
        self.assertIn("casier hors des dimensions", res.stderr.lower())

    def test_21_armoire_casier_doublon(self):
        """Casier en double dans l'armoire -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.scenario_normal,
            self.casses_dir / "donnees_armoire_doublon",
        )
        self.assertIn("casier en double", res.stderr.lower())

    def test_22_armoire_etiquette_incoherente(self):
        """Etiquette d'un casier incoherente avec sa position -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.scenario_normal,
            self.casses_dir / "donnees_armoire_etiquette_incoherente",
        )
        self.assertIn("etiquette incoherente", res.stderr.lower())

    def test_23_dico_emotion_inconnue(self):
        """Dictionnaire avec une emotion inconnue -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.scenario_normal,
            self.casses_dir / "donnees_dico_emotion_inconnue",
        )
        self.assertIn("emotion inconnue", res.stderr.lower())

    def test_24_dico_intensite_inconnue(self):
        """Dictionnaire avec une intensite inconnue -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.scenario_normal,
            self.casses_dir / "donnees_dico_intensite_inconnue",
        )
        self.assertIn("intensite inconnue", res.stderr.lower())

    def test_25_dico_mot_doublon(self):
        """Dictionnaire avec le meme mot dans deux entrees -> echec propre."""
        res = self._executer_agent(
            self.carte_normale,
            self.scenario_normal,
            self.casses_dir / "donnees_dico_mot_doublon",
        )
        self.assertIn("meme mot dans deux entrees", res.stderr.lower())

    def test_26_arguments_insuffisants(self):
        """Nombre d'arguments incorrect sur agent.py -> code de retour 2 et message d'usage."""
        res = subprocess.run(
            [sys.executable, str(self.agent_py)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        self.assertIn("usage", res.stderr.lower())
        self.assertNotIn("Traceback", res.stderr)


if __name__ == "__main__":
    unittest.main()
