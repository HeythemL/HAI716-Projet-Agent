import json
import unicodedata


def normaliser(texte):
    """Decoupe un message en minuscules, sans accents, lettres uniquement."""
    texte_sans_accents = unicodedata.normalize("NFD", texte.lower())
    texte_pur = "".join(c for c in texte_sans_accents if unicodedata.category(c) != "Mn")
    
    mots = []
    mot_courant = ""
    for c in texte_pur:
        if c.isalpha():
            mot_courant += c
        else:
            if mot_courant != "":
                mots.append(mot_courant)
                mot_courant = ""
    if mot_courant != "":
        mots.append(mot_courant)
    return mots


def construire_index(donnees):
    """Construit un dictionnaire forme -> (emotion, intensite)."""
    index = {}
    if isinstance(donnees, dict):
        entrees = donnees.get("entrees", [])
    else:
        entrees = donnees

    for entree in entrees:
        emotion = entree["emotion"]
        intensite = entree["intensite"]
        for forme in entree.get("formes", []):
            index[forme] = (emotion, intensite)
    return index


def charger_index(chemin_fichier):
    """Charge le dictionnaire JSON et construit l'index."""
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        donnees = json.load(f)
    return construire_index(donnees)


def lire_emotion(message, index):
    """Cherche le premier mot du message present dans le dictionnaire."""
    mots = normaliser(message)
    for mot in mots:
        if mot in index:
            return index[mot]
    return None


class LecteurEmotion:
    """Permet de charger le dictionnaire et d'analyser les messages."""

    def __init__(self, source):
        if isinstance(source, dict) and "entrees" in source:
            self.index = construire_index(source)
        elif isinstance(source, dict):
            self.index = source
        else:
            self.index = charger_index(source)

    def identifier(self, message):
        return lire_emotion(message, self.index)
