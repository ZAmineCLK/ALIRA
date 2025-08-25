# utils/dependencies.py
import sys
import subprocess
import importlib
from .logger import logger

def installer_module(nom_module, nom_import=None, option_install=None):
    if nom_import is None:
        nom_import = nom_module
    
    try:
        importlib.import_module(nom_import)
        logger.info(f"{nom_module} est déjà installé")
        return True
    except ImportError:
        logger.info(f"{nom_module} n'est pas installé. Installation en cours...")
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if option_install:
                cmd.append(option_install)
            cmd.append(nom_module)
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"{nom_module} installé avec succès")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Échec de l'installation de {nom_module}: {e.stderr}")
            return False

def verifier_et_installer_dependances():
    logger.info("Vérification des dépendances...")
    
    dependances = [
        ("spacy", "spacy", None),
        ("chatterbot", "chatterbot", None),
        ("chatterbot-corpus", "chatterbot_corpus", None),
        ("mysql-connector-python", "mysql.connector", None),
        ("python-dotenv", "dotenv", None),
        ("requests", "requests", None),
        ("torch", "torch", None),
        ("transformers", "transformers", None),
        ("sentence-transformers", "sentence_transformers", None),
        ("accelerate", "accelerate", None)
    ]
    
    for nom_pip, nom_import, option in dependances:
        if not installer_module(nom_pip, nom_import, option):
            logger.error(f"Dépendance critique manquante: {nom_pip}")
            return False
    
    return True

def verifier_modele_spacy(nom_modele="fr_core_news_sm"):
    try:
        import spacy
        try:
            spacy.load(nom_modele)
            logger.info(f"Modèle spaCy '{nom_modele}' est déjà installé")
            return True
        except OSError:
            logger.info(f"Modèle spaCy '{nom_modele}' non trouvé. Installation...")
            try:
                cmd = [sys.executable, "-m", "spacy", "download", nom_modele]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info(f"Modèle '{nom_modele}' installé avec succès")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Échec de l'installation du modèle: {e.stderr}")
                return False
    except ImportError:
        return False