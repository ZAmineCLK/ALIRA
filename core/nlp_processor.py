# core/nlp_processor.py
from utils.logger import logger

def initialiser_spacy():
    try:
        import spacy
        nlp = spacy.load("fr_core_news_sm")
        logger.info("spaCy initialisé avec succès")
        return nlp
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de spaCy: {e}")
        return None