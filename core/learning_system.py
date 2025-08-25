# core/learning_system.py
import json
import re
import random
from typing import List, Dict, Tuple, Optional
from utils.logger import logger
from utils.text_processing import corriger_fautes_typo, normaliser_question, nettoyer_question_pour_recherche
from storage.mysql_manager import MySQLManager
from models.local_models import ModeleLocal
from core.assistant_model import AssistantPhaseBebe
from config.settings import PROJECT_NAME, LEARNING_CONFIG

class SystemeApprentissage:
    def __init__(self, nlp=None):
        self.nlp = nlp
        self.mysql_manager = MySQLManager()
        self.modele_local = ModeleLocal(nlp)
        self.assistant_bebe = AssistantPhaseBebe(nlp)
        self.phase_bebe_active = LEARNING_CONFIG['phase_bebe_active']
        self.seuil_autonomie = LEARNING_CONFIG['seuil_autonomie']
        
        self.mots_cles_apprentissage = {
            'apprends': ['apprends', 'enseigne', 'souviens', 'mémorise', 'retiens', 'learn', 'teach', 'remember'],
            'corrige': ['corrige', 'change', 'modifie', 'erreur', 'faux', 'correct', 'wrong', 'mistake'],
            'oublie': ['oublie', 'supprime', 'efface', 'retire', 'forget', 'delete', 'remove']
        }
    
    # ... [Les méthodes restantes de SystemeApprentissage]
    # Les méthodes seront organisées par fonctionnalité