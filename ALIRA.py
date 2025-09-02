#!/usr/bin/env python3
"""
ALIRA 1.0 PALLAS - Accompagnante Libre à Interaction et Réflexion Assistée
Inspirée par la sagesse des nymphes guides - Version stable avec templates éprouvés
"""

import sys
import subprocess
import importlib
import re
import json
import os
import datetime
import random
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import dotenv
import requests
from urllib.parse import quote
import time
import torch
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alira.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ALIRA")

# Charger les variables d'environnement
dotenv.load_dotenv()

# ---------------------------------------------------------
# CONFIGURATION GLOBALE - NOUVELLE IDENTITÉ ALIRA
# ---------------------------------------------------------
PROJECT_NAME = "ALIRA"
FULL_NAME = "Accompagnante Libre à Interaction et Réflexion Assistée"
MYTHOLOGICAL_SUBTITLE = "Inspirée par la sagesse des nymphes guides"
VERSION = "1.0 Pallas"  # Référence à Athéna Pallas

# Signature ASCII artistique
SIGNATURE = r"""
    ___    _    _    ___    ___ 
   / _ \  | |  | |  | _ \  | _ \
  | | | | | |  | |  |  _/  |  _/
  | |_| | | |__| |  | |__  | |  
   \___/  \____/   |____| |_|  
"""

# Thème mythologique
MYTHOLOGICAL_THEME = {
    'wisdom': "À l'image d'Athéna, je cherche la sagesse et la connaissance",
    'guidance': "Comme les nymphes guides de la mythologie, je vous accompagne", 
    'protection': "Tel un bouclier divin, je protège votre parcours d'apprentissage",
    'learning': "Comme Prométhée apportant le feu, j'allume l'étincelle du savoir"
}

# Seuils d'autonomie
SEUILS_AUTONOMIE = {
    'bebe_vers_apprentissage': 20,
    'apprentissage_vers_adulte': 100,
    'taux_utilisation_modele_adulte': 0.1
}

# Couleurs pour l'interface
class Couleurs:
    BLEU = '\033[94m'
    VERT = '\033[92m'
    ORANGE = '\033[93m'
    ROUGE = '\033[91m'
    FIN = '\033[0m'
    GRAS = '\033[1m'

def afficher_avec_style(texte, couleur=None, gras=False):
    """Affiche du texte avec style"""
    style = ""
    if couleur:
        style += couleur
    if gras:
        style += Couleurs.GRAS
    return f"{style}{texte}{Couleurs.FIN}" if style else texte

# ---------------------------------------------------------
# 1. GESTION DES DÉPENDANCES
# ---------------------------------------------------------

def installer_module(nom_module, nom_import=None, option_install=None):
    """Tente d'importer un module et l'installe si absent"""
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
    """Vérifie et installe toutes les dépendances nécessaires"""
    logger.info("Vérification des dépendances...")
    
    # SUPPRIMER chatterbot et chatterbot-corpus des dépendances
    dependances = [
        ("spacy", "spacy", None),
        ("mysql-connector-python", "mysql.connector", None),
        ("python-dotenv", "dotenv", None),
        ("requests", "requests", None),
        ("torch", "torch", None),
        ("transformers", "transformers", None),
    ]
    
    for nom_pip, nom_import, option in dependances:
        if not installer_module(nom_pip, nom_import, option):
            logger.error(f"Dépendance critique manquante: {nom_pip}")
            return False
    
    return True

def verifier_modele_spacy(nom_modele="fr_core_news_sm"):
    """Vérifie si le modèle spaCy français est installé, sinon l'installe"""
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
                try:
                    nom_modele_pip = nom_modele.replace("_", "-")
                    cmd = [sys.executable, "-m", "pip", "install", nom_modele_pip]
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    logger.info("Modèle installé via pip alternative")
                    return True
                except subprocess.CalledProcessError:
                    logger.error("Échec de l'installation via pip alternative")
                    return False
    except ImportError:
        return False

# ---------------------------------------------------------
# 2. CONFIGURATION MYSQL
# ---------------------------------------------------------

class MySQLConfig:
    """Configuration et gestion de la connexion MySQL"""
    
    @staticmethod
    def get_connection_config():
        """Retourne la configuration de connexion"""
        return {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'database': os.getenv('MYSQL_DATABASE', 'alira_db'),
            'user': os.getenv('MYSQL_USER', 'alira_user'),
            'password': os.getenv('MYSQL_PASSWORD', 'alira_password'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True
        }
    
    @staticmethod
    def test_connection():
        """Teste la connexion MySQL"""
        try:
            config = MySQLConfig.get_connection_config()
            connection = mysql.connector.connect(**config)
            if connection.is_connected():
                logger.info("Connexion MySQL réussie")
                connection.close()
                return True
        except Error as e:
            logger.error(f"Erreur de connexion MySQL: {e}")
            return False
    
    @staticmethod
    def setup_database():
        """Crée la base de données et les tables si nécessaire"""
        try:
            config = MySQLConfig.get_connection_config()
            database_name = config.pop('database')
            
            # Connexion sans spécifier la base de données pour la créer
            temp_config = config.copy()
            if 'database' in temp_config:
                del temp_config['database']
                
            connection = mysql.connector.connect(**temp_config)
            cursor = connection.cursor()
            
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {database_name}")
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS chatbot_memory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_normalized VARCHAR(255) NOT NULL UNIQUE,
                response TEXT NOT NULL,
                variations JSON,
                learn_count INT DEFAULT 0,
                use_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_question (question_normalized),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_table_query)
            
            create_history_query = """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_history_query)
            
            create_stats_query = """
            CREATE TABLE IF NOT EXISTS learning_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stat_key VARCHAR(50) NOT NULL UNIQUE,
                stat_value INT DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_stats_query)
            
            stats_data = [
                ('apprentissages', 0),
                ('apprentissages_auto', 0),
                ('corrections', 0),
                ('suppressions', 0),
                ('total_conversations', 0),
                ('phase_bebe', 1),
                ('niveau_autonomie', 0)
            ]
            
            for stat_key, stat_value in stats_data:
                cursor.execute("INSERT IGNORE INTO learning_stats (stat_key, stat_value) VALUES (%s, %s)", 
                              (stat_key, stat_value))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info("Base de données MySQL configurée avec succès")
            return True
            
        except Error as e:
            logger.error(f"Erreur configuration MySQL: {e}")
            return False

# ---------------------------------------------------------
# 3. FONCTIONS UTILITAIRES
# ---------------------------------------------------------

def corriger_fautes_typo(phrase):
    """Correction des fautes de frappe courantes"""
    if not phrase:
        return phrase
        
    corrections = {
        'aprend': 'apprend', 'aprens': 'apprend', 'aprends': 'apprend',
        'souven': 'souviens', 'souvenz': 'souviens',
        'mémori': 'mémorise', 'memorise': 'mémorise',
        'reten': 'retiens', 'retien': 'retiens',
        'corect': 'corrige', 'corection': 'correction',
        'change': 'corrige', 'modifi': 'modifie',
        'oubli': 'oublie', 'oublie': 'oublie',
        'supri': 'supprime', 'supression': 'suppression',
        'eface': 'efface', 'effas': 'efface',
        'c\'ast': 'c\'est', 'c est': 'c\'est', 'cest': 'c\'est',
        'paris': 'Paris', 'france': 'France',
        'capital': 'capitale', 'capitale': 'capitale',
        'ville': 'ville', 'pay': 'pays',
        'veut': 'veux', 'discuté': 'discuter', 'voyagé': 'voyager',
        'trouv': 'trouve', 'ce trouve': 'se trouve'
    }
    
    phrase_corrigee = phrase
    for faute, correction in corrections.items():
        phrase_corrigee = re.sub(r'\b' + faute + r'\b', correction, phrase_corrigee, flags=re.IGNORECASE)
    
    return phrase_corrigee

def normaliser_question(question):
    """Normalise les questions pour meilleure reconnaissance"""
    if not question:
        return question
        
    normalisations = {
        r'c\'est quoi\s+': 'qu\'est-ce que ',
        r'que veut dire\s+': 'définition ',
        r'quel est\s+': 'définition ',
        r'quelle est\s+': 'définition ',
        r'quels sont\s+': 'définition ',
        r'explique\s+': 'définition ',
        r'définis\s+': 'définition ',
        r'dis moi\s+': 'définition ',
        r'connais tu\s+': 'définition ',
        r'sais tu\s+': 'définition ',
        r'\bville de\b': '',
        r'\ble\b': '', r'\bla\b': '', r'\bles\b': '', r'\bdes\b': '',
        r'\bdu\b': '', r'\bde\b': '', r'\bun\b': '', r'\bune\b': ''
    }
    
    question_normalisee = question.lower()
    for pattern, remplacement in normalisations.items():
        question_normalisee = re.sub(pattern, remplacement, question_normalisee, flags=re.IGNORECASE)
    
    question_normalisee = re.sub(r'\s+', ' ', question_normalisee).strip()
    return question_normalisee

def nettoyer_question_pour_recherche(question):
    """Nettoie une question en supprimant les formules de politesse pour la recherche"""
    if not question:
        return question
    
    motifs_a_supprimer = [
        r'^bonjour\s*,?\s*', r'^salut\s*,?\s*', r'^hello\s*,?\s*', r'^hi\s*,?\s*',
        r'^coucou\s*,?\s*', r'^merci\s*,?\s*', r'^thank you\s*,?\s*', r'^thanks\s*,?\s*',
        r'\s*s\'il vous plaît\s*', r'\s*please\s*', r'^dis moi\s*,?\s*', r'^tell me\s*,?\s*'
    ]
    
    question_nettoyee = question
    for motif in motifs_a_supprimer:
        question_nettoyee = re.sub(motif, '', question_nettoyee, flags=re.IGNORECASE)
    
    question_nettoyee = re.sub(r'\s+', ' ', question_nettoyee).strip()
    return question_nettoyee

def preparer_question_pour_modele(question):
    """Nettoie et formate la question pour le modèle"""
    if not question:
        return ""
    
    # Supprimer les formules de politesse
    question = nettoyer_question_pour_recherche(question)
    
    # Corriger les fautes de frappe courantes
    question = corriger_fautes_typo(question)
    
    # Normaliser la question
    question = normaliser_question(question)
    
    return question

# ---------------------------------------------------------
# 4. COUCHE MÉMOIRE PERSISTANTE
# ---------------------------------------------------------

class CoucheMemoireMySQL:
    """Gère la mémoire persistante avec MySQL"""
    
    def __init__(self):
        self.connection = self._get_connection()
        self.initialiser_connaissances_de_base()
    
    def _get_connection(self):
        """Établit une connexion MySQL"""
        try:
            config = MySQLConfig.get_connection_config()
            connection = mysql.connector.connect(**config)
            return connection
        except Error as e:
            logger.error(f"Erreur connexion MySQL: {e}")
            return None
    
    def initialiser_connaissances_de_base(self):
        """Initialise les connaissances de base mythologiques"""
        connaissances_base = [
            ("bonjour", "Salutations ! Je suis ALIRA, votre guide inspirée par la sagesse des nymphes."),
            ("parents", "Les parents sont comme des divinités protectrices qui guident et élèvent leurs enfants avec amour et sagesse."),
            ("qu'est-ce que parents", "Les parents sont ceux qui donnent la vie et guident comme des mentors bienveillants, à l'image de Zeus et Héra."),
            ("définition de parents", "Êtres qui procréent et élèvent leur progéniture, formant le fondement de la famille comme les colonnes d'un temple."),
            ("que sont les parents", "Les parents sont les piliers familiaux, offrant protection et guidance tel un bouclier divin."),
            ("nymphes", "Les nymphes sont des divinités mineures de la nature dans la mythologie grecque, souvent associées aux forêts, montagnes et cours d'eau."),
            ("que veut dire nymphes", "Les nymphes sont des esprits féminins de la nature dans la mythologie grecque, représentant les forces vitales de la nature."),
        ]
        
        for question, reponse in connaissances_base:
            self.sauvegarder_connaissance(question, reponse, "init")
        
        logger.info(f"Connaissances de base initialisées: {len(connaissances_base)}")
    
    def consulter_memoire(self, question):
        """Consulte la mémoire pour une question"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = self._get_connection()
                
            question_normalisee = normaliser_question(question)
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, response FROM chatbot_memory WHERE question_normalized = %s", 
                          (question_normalisee,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                self._incrementer_utilisation(result['id'])
                return result['response']
            return None
                
        except Error as e:
            logger.error(f"Erreur consultation mémoire: {e}")
            return None
    
    def _incrementer_utilisation(self, memory_id):
        """Incrémente le compteur d'utilisation"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE chatbot_memory SET use_count = use_count + 1 WHERE id = %s", 
                          (memory_id,))
            self.connection.commit()
            cursor.close()
        except Error as e:
            logger.error(f"Erreur incrémentation utilisation: {e}")
    
    def sauvegarder_connaissance(self, question, reponse, source="manuelle"):
        """Sauvegarde une nouvelle connaissance"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = self._get_connection()
                
            question_normalisee = normaliser_question(question)
            
            cursor = self.connection.cursor()
            query = """
            INSERT INTO chatbot_memory (question_normalized, response, learn_count)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE 
                response = VALUES(response),
                learn_count = learn_count + 1
            """
            cursor.execute(query, (question_normalisee, reponse))
            self.connection.commit()
            cursor.close()
            
            self._incrementer_statistique('apprentissages')
            if source != "manuelle":
                self._incrementer_statistique('apprentissages_auto')
                
            return True
        except Error as e:
            logger.error(f"Erreur sauvegarde connaissance: {e}")
            return False
    
    def _incrementer_statistique(self, stat_key):
        """Incrémente une statistique"""
        try:
            cursor = self.connection.cursor()
            query = "UPDATE learning_stats SET stat_value = stat_value + 1 WHERE stat_key = %s"
            cursor.execute(query, (stat_key,))
            self.connection.commit()
            cursor.close()
        except Error as e:
            logger.error(f"Erreur mise à jour statistique: {e}")
    
    def get_nombre_connaissances(self):
        """Retourne le nombre de connaissances en mémoire"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM chatbot_memory")
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else 0
        except Error as e:
            logger.error(f"Erreur comptage connaissances: {e}")
            return 0
    
    def get_niveau_autonomie(self):
        """Retourne le niveau d'autonomie actuel"""
        nb_connaissances = self.get_nombre_connaissances()
        
        if nb_connaissances < SEUILS_AUTONOMIE['bebe_vers_apprentissage']:
            return "bebe"
        elif nb_connaissances < SEUILS_AUTONOMIE['apprentissage_vers_adulte']:
            return "apprentissage"
        else:
            return "adulte"

# ---------------------------------------------------------
# 5. COUCHE VALIDATION
# ---------------------------------------------------------

class CoucheValidationStricte:
    """Valide strictement les réponses générées"""
    
    def __init__(self, nlp=None):
        self.nlp = nlp
    
    def valider_reponse(self, reponse, question_originale):
        """Valide une réponse selon plusieurs critères"""
        if not reponse:
            return False
        
        # Longueur minimale adaptée
        if len(reponse) < 8:
            logger.warning("Réponse trop courte")
            return False
        
        reponse_lower = reponse.lower()
        
        # Rejeter les réponses de fallback
        phrases_fallback = [
            "enseignez-moi cette connaissance",
            "pouvez-vous m'éclairer",
            "racontez-moi son histoire",
            "je dois encore apprendre",
            "aidez-moi dans cette quête",
            "comme les dieux apprennent"
        ]
        
        if any(phrase in reponse_lower for phrase in phrases_fallback):
            logger.warning("Réponse identifiée comme fallback")
            return False
        
        # Patterns absolument inacceptables
        patterns_interdits = [
            r'il t te das', r'il t te', r'te das', r'^[^a-zàâäéèêëîïôöùûüç]*$',
            r'repeat', r'again', r'what do you mean', r'can you explain',
            r'je ne comprends pas', r'je sais pas', r'pouvez-vous répéter'
        ]
        
        for pattern in patterns_interdits:
            if re.search(pattern, reponse_lower):
                logger.warning("Réponse contient des patterns inacceptables")
                return False
        
        # Validation moins stricte pour les réponses mythologiques
        mots_mythologiques = ['sagesse', 'antique', 'grec', 'myth', 'oracle', 'dieu', 'déesse', 'divin', 'nature']
        if any(mot in reponse_lower for mot in mots_mythologiques):
            return True
        
        # Vérification de cohérence basique
        return self.est_pertinente(reponse, question_originale)
    
    def est_pertinente(self, reponse, question):
        """Vérifie la pertinence sémantique"""
        if not question or not reponse:
            return False
        
        mots_question = set(question.lower().split())
        mots_reponse = set(reponse.lower().split())
        
        stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'est', 'que', 'quoi', 'c\'est'}
        
        mots_communs = mots_question.intersection(mots_reponse) - stop_words
        return len(mots_communs) > 0

# ---------------------------------------------------------
# 6. COUCHE TEMPLATES STABLES (VERSION FIABLE - CORRIGÉE)
# ---------------------------------------------------------

class CoucheTemplatesStables:
    """Gère EXCLUSIVEMENT des templates stables et éprouvés"""
    
    def __init__(self, nlp=None):
        self.nlp = nlp
        self.modele_charge = True  # Les templates sont toujours disponibles
        self._initialiser_templates()
    
    def _initialiser_templates(self):
        """Initialise les templates de réponse stables"""
        self.templates = {
            'definition': [
                "{} évoque la sagesse des anciens, comme les mystères que les initiés contemplaient.",
                "Le concept de {} trouve son écho dans la philosophie antique et la mythologie.",
                "{} représente un principe fondamental que les sages de l'Antiquité étudiaient.",
                "Dans la tradition, {} symbolise des forces naturelles ou spirituelles importantes.",
                "{} incarne des qualités que les mythologies associent souvent aux divinités.",
                "{} nous connecte à l'essence divine que les mythologies explorent depuis des millénaires.",
                "La notion de {} résonne avec les archétypes universels des mythes fondateurs."
            ],
            'biographie': [
                "{} incarne des qualités héroïques qui rappellent les figures légendaires de la mythologie.",
                "Comme les héros mythologiques, {} inspire par son parcours unique et remarquable.",
                "{} possède une aura qui évoque les demi-dieux et héroïnes de l'Antiquité.",
                "Le destin de {} mériterait d'être chanté par les poètes comme les épopées homériques."
            ],
            'procedure': [
                "Pour {}, on peut s'inspirer des arts mystérieux des anciens initiés et des artisans.",
                "{} demande la patience et la précision des artisans qui forgeaient les armes des héros.",
                "Comme les rituels sacrés, {} suit un cheminement précis vers la maîtrise et la sagesse.",
                "La réalisation de {} évoque les quêtes mythiques où chaque étape apporte son enseignement."
            ]
        }
    
    def _extraire_terme_principal(self, question):
        """Extrait le terme principal de la question"""
        question_lower = question.lower()
        
        # Supprimer les mots interrogatifs
        motifs_a_supprimer = [
            r'que veut dire', r'qu\'est ce que', r'qu\'est-ce que', 
            r'c\'est quoi', r'définition de', r'explique moi'
        ]
        
        terme = question_lower
        for motif in motifs_a_supprimer:
            terme = re.sub(motif, '', terme, flags=re.IGNORECASE)
        
        terme = re.sub(r'[?¿]', '', terme).strip()
        return terme.capitalize() if terme else question
    
    def generer_reponse_fiable(self, question):
        """Génération via templates 100% fiables"""
        question_lower = question.lower()
        terme = self._extraire_terme_principal(question)
        
        # Déterminer le type de question
        if any(mot in question_lower for mot in ['quoi', 'qu\'est', 'défini', 'c\'est quoi', 'que veut dire', 'définition', 'explique']):
            return self._generer_definition(terme)
        elif any(mot in question_lower for mot in ['qui', 'personne', 'histoire de']):
            return self._generer_biographie(terme)
        elif any(mot in question_lower for mot in ['comment', 'faire', 'procédé']):
            return self._generer_procedure(terme)
        else:
            return self._reponse_fallback(question)
    
    def _generer_definition(self, terme):
        """Génère une définition mythologique"""
        if not terme:
            return self._reponse_fallback("définition")
        
        template = random.choice(self.templates['definition'])
        return template.format(terme)
    
    def _generer_biographie(self, terme):
        """Génère une biographie mythologique"""
        if not terme:
            return self._reponse_fallback("biographie")
        
        template = random.choice(self.templates['biographie'])
        return template.format(terme)
    
    def _generer_procedure(self, terme):
        """Génère une procédure mythologique"""
        if not terme:
            return self._reponse_fallback("procédure")
        
        template = random.choice(self.templates['procedure'])
        return template.format(terme)
    
    def _reponse_fallback(self, question):
        """Réponses de fallback améliorées"""
        question_lower = question.lower()
        
        # Détection de type de question
        if any(mot in question_lower for mot in ['quoi', 'qu\'est', 'défini']):
            return "Comme l'Oracle face à une énigme, je cherche encore la sagesse sur ce sujet. Pouvez-vous m'éclairer ?"
        
        elif any(mot in question_lower for mot in ['qui', 'personne', 'quelqu\'un']):
            return "Cette figure mythique ou contemporaine m'est encore inconnue. Racontez-moi son histoire !"
        
        elif any(mot in question_lower for mot in ['comment', 'faire', 'procédé']):
            return "Tel un artisan devant son œuvre, je dois encore apprendre cet art. Enseignez-moi !"
        
        elif any(mot in question_lower for mot in ['pourquoi', 'cause', 'raison']):
            return "Comme les philosophes grecs, je médite sur les causes premières. Aidez-moi dans cette quête !"
        
        # Réponse générale
        return "Comme les dieux apprennent des mortels, enseignez-moi cette connaissance que je pourrai partager !"

# ---------------------------------------------------------
# 7. COUCHE APPRENTISSAGE AUTOMATIQUE
# ---------------------------------------------------------

class CoucheApprentissageAutomatique:
    """Gère l'apprentissage automatique"""
    
    def __init__(self, couche_memoire):
        self.memoire = couche_memoire
    
    def apprendre_automatiquement(self, question, reponse):
        """Décide si on doit apprendre automatiquement"""
        if not question or not reponse:
            return False
        
        if len(reponse) < 20:
            return False
        
        phrases_exclues = [
            "je ne sais pas", "i don't know", "désolé", "sorry", 
            "pouvez-vous reformuler", "can you rephrase",
            "c'est pas faux", "on est pas mal",
            "enseignez-moi", "pouvez-vous m'éclairer", "racontez-moi"
        ]
        
        reponse_lower = reponse.lower()
        if any(phrase in reponse_lower for phrase in phrases_exclues):
            return False
        
        return self.memoire.sauvegarder_connaissance(question, reponse, "auto")
    
    def devrait_apprendre(self, question, reponse):
        """Décide si la réponse mérite d'être apprise"""
        if len(reponse) < 20:
            return False
        
        mots_substantifs = sum(1 for mot in reponse.split() if len(mot) > 3)
        return mots_substantifs >= 3

# ---------------------------------------------------------
# 8. COUCHE ORCHESTRATION ROBUSTE
# ---------------------------------------------------------

class CoucheOrchestrationRobuste:
    """Orchestration axée FIABILITÉ"""
    
    def __init__(self):
        self.couches = {}
        self.niveau_autonomie = "bebe"
        self.debug_mode = True
        self.modele_disponible = False
    
    def connecter_couches(self, memoire, validation, apprentissage, modeles):
        """Connecte les couches avec vérification de stabilité"""
        self.couches = {
            'memoire': memoire,
            'validation': validation,
            'apprentissage': apprentissage,
            'modeles': modeles
        }
        self.modele_disponible = modeles.modele_charge
        self._mettre_a_jour_autonomie()
        
        logger.info(f"🔧 Modèle disponible: {self.modele_disponible}")
    
    def _mettre_a_jour_autonomie(self):
        """Met à jour le niveau d'autonomie"""
        if 'memoire' in self.couches:
            self.niveau_autonomie = self.couches['memoire'].get_niveau_autonomie()
    
    def _rechercher_wikipedia(self, question):
        """Recherche sur Wikipedia avec gestion d'erreurs améliorée"""
        try:
            # Nettoyer la question pour la recherche
            question_propre = nettoyer_question_pour_recherche(question)
            if not question_propre or len(question_propre) < 3:
                return None
            
            # API Wikipedia REST avec timeout court
            url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{quote(question_propre)}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data and data['extract']:
                    extract = data['extract'].strip()
                    if extract and len(extract) > 30:
                        return extract[:350] + "..." if len(extract) > 350 else extract
            
            # Si pas de résultat direct, tentative avec recherche
            return self._rechercher_wikipedia_alternative(question_propre)
                
        except requests.exceptions.Timeout:
            if self.debug_mode:
                print("⏰ [DEBUG] Wikipedia timeout")
            return None
        except requests.exceptions.ConnectionError:
            if self.debug_mode:
                print("🌐 [DEBUG] Wikipedia connexion impossible")
            return None
        except Exception as e:
            if self.debug_mode:
                print(f"❓ [DEBUG] Erreur Wikipedia: {e}")
            return None
    
    def _rechercher_wikipedia_alternative(self, terme):
        """Recherche alternative avec l'API de recherche"""
        try:
            # API de recherche si le summary direct échoue
            search_url = f"https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(terme)}&format=json&utf8=1"
            response = requests.get(search_url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if 'query' in data and 'search' in data['query'] and data['query']['search']:
                    premier_resultat = data['query']['search'][0]['title']
                    # Maintenant on récupère le summary du premier résultat
                    return self._rechercher_wikipedia(premier_resultat)
                    
        except Exception:
            pass
        
        return None
    
    def _rechercher_base_connaissances(self, question):
        """Recherche dans la base de connaissances intégrée"""
        connaissances_base = {
            'maman': 'Une mère est comme une déesse protectrice, elle donne naissance et élève ses enfants avec amour',
            'paris': 'Paris est la capitale de la France, telle Athéna protégeant Athènes',
            'france': 'La France est un pays d\'Europe, berceau de nombreuses légendes modernes',
            'intelligence artificielle': 'Domaine prométhéen qui apporte le feu de la connaissance à l\'humanité',
            'bébé': 'Un jeune enfant, pur comme les héros au début de leur quête',
            'papa': 'Un père est un pilier familial, tel Zeus guidant les dieux de l\'Olympe',
            'famille': 'Groupe uni par les liens du sang et de l\'affection, comme les dieux grecs',
            'ordinateur': 'Machine moderne qui accomplit des prodiges dignes des inventions d\'Héphaïstos',
            'internet': 'Réseau mondial qui connecte l\'humanité, tel Hermes messager des dieux',
            'apprendre': 'Processus sacré d\'acquisition de connaissances, comme les mystères d\'Eleusis',
            'mythologie': 'Étude des récits légendaires qui fondent nos civilisations et notre imaginaire',
            'grèce': 'Berceau de la démocratie et de la philosophie, terre des dieux et des héros',
            'athéna': 'Déesse de la sagesse, de la stratégie militaire et des arts, née du crâne de Zeus',
            'zeus': 'Roi des dieux dans la mythologie grecque, maître du tonnerre et de l\'Olympe',
            'déesse': 'Être divin féminin dans les mythologies, souvent associé à la nature, la fertilité ou la sagesse',
            'oracle': 'Personne ou lieu through lequel les dieux communiquaient des prophéties dans la mythologie grecque',
            'divine': 'Ce qui relève de la nature des dieux, de l\'essence sacrée et transcendante',
            'nature': 'Le monde naturel que les anciens vénéraient comme manifestation du divin'
        }
        
        question_lower = question.lower()
        for mot, reponse in connaissances_base.items():
            if mot in question_lower:
                return reponse
        
        return None
    
    def traiter_question(self, question):
        """Traite une question avec l'ordre CORRECT"""
        if not question:
            return "Veuillez poser une question."
        
        self._mettre_a_jour_autonomie()
        
        # 1. ✅ CONSULTATION MÉMOIRE PRIORITAIRE
        if reponse_memoire := self.couches['memoire'].consulter_memoire(question):
            if self.debug_mode:
                print(f"🔍 [DEBUG] Trouvé en mémoire: {reponse_memoire}")
            return reponse_memoire
        
        # 2. Préparer la question pour le modèle
        question_preparee = preparer_question_pour_modele(question)
        
        # 3. ❓ DÉLÉGATION CONTRÔLÉE AUX TEMPLATES
        reponse_modele = None
        if self.modele_disponible:
            reponse_modele = self.couches['modeles'].generer_reponse_fiable(question_preparee)
            
            if reponse_modele and self.debug_mode:
                print(f"🤖 [DEBUG] Réponse modèle: '{reponse_modele}'")
            
            if reponse_modele and self.couches['validation'].valider_reponse(reponse_modele, question):
                if self.debug_mode:
                    print(f"✅ [DEBUG] Réponse validée: '{reponse_modele}'")
                
                if self.couches['apprentissage'].devrait_apprendre(question, reponse_modele):
                    self.couches['apprentissage'].apprendre_automatiquement(question, reponse_modele)
                
                return reponse_modele
            else:
                if self.debug_mode:
                    print(f"❌ [DEBUG] Réponse rejetée par la validation")
        
        # 4. 🌐 RECHERCHE WIKIPEDIA (TOUJOURS tentée après échec modèle)
        if reponse_wiki := self._rechercher_wikipedia(question):
            if self.debug_mode:
                print(f"🌐 [DEBUG] Réponse Wikipedia: '{reponse_wiki}'")
            
            # Validation de la réponse Wikipedia aussi
            if self.couches['validation'].valider_reponse(reponse_wiki, question):
                if self.couches['apprentissage'].devrait_apprendre(question, reponse_wiki):
                    self.couches['apprentissage'].apprendre_automatiquement(question, reponse_wiki)
                return reponse_wiki
            elif self.debug_mode:
                print(f"❌ [DEBUG] Réponse Wikipedia rejetée par la validation")
        
        # 5. 📚 BASE DE CONNAISSANCES INTERNE (fallback)
        if reponse_base := self._rechercher_base_connaissances(question):
            if self.debug_mode:
                print(f"📚 [DEBUG] Réponse base: '{reponse_base}'")
            if self.couches['apprentissage'].devrait_apprendre(question, reponse_base):
                self.couches['apprentissage'].apprendre_automatiquement(question, reponse_base)
            return reponse_base
        
        # 6. 💬 RÉPONSE PAR DÉFAUT (seulement si tout échoue)
        return self._reponse_par_defaut(question)
    
    def _reponse_par_defaut(self, question):
        """Réponse par défaut quand on ne sait pas"""
        reponses_mythologiques = [
            "Comme l'Oracle de Delphes, je perçois votre question mais cherche encore la réponse...",
            "Tel un héros face à une énigme, je dois encore apprendre ce savoir.",
            "Cette connaissance m'échappe encore, à l'image des mystères non résolus de l'Antiquité.",
            "Comme les dieux qui apprenaient des mortels, enseignez-moi cette sagesse.",
            "Tel Thésée dans le labyrinthe, je cherche le fil de la connaissance qui me mènera à la réponse.",
            "Comme les Muses inspirent les artistes, inspirez-moi la réponse à votre question."
        ]
        
        if self.niveau_autonomie == "bebe":
            return "👶 " + random.choice(reponses_mythologiques) + " Pouvez-vous m'apprendre ?"
        else:
            return random.choice(reponses_mythologiques) + " Voulez-vous m'enseigner cela ?"
    
    def get_niveau_autonomie(self):
        """Retourne le niveau d'autonomie actuel"""
        return self.niveau_autonomie
    
    def get_statistiques(self):
        """Retourne les statistiques"""
        if 'memoire' in self.couches:
            nb_connaissances = self.couches['memoire'].get_nombre_connaissances()
            modele_info = "avec templates" if self.modele_disponible else "sans templates"
            
            niveaux_mythologiques = {
                "bebe": "🐣 Novice (comme un jeune héros)",
                "apprentissage": "🧒 Apprenti (comme un demi-dieu en formation)", 
                "adulte": "🏛️ Sage (comme un oracle)"
            }
            
            niveau = niveaux_mythologiques.get(self.niveau_autonomie, self.niveau_autonomie)
            return f"📊 {niveau} | Connaissances: {nb_connaissances} | {modele_info}"
        return "📊 Statistiques non disponibles"
    
    def toggle_debug(self):
        """Active/désactive le mode debug"""
        self.debug_mode = not self.debug_mode
        statut = "ACTIVÉ" if self.debug_mode else "DÉSACTIVÉ"
        print(f"🔍 Mode debug {statut}")
        return self.debug_mode

# ---------------------------------------------------------
# 9. INITIALISATION DES COMPOSANTS
# ---------------------------------------------------------

def initialiser_spacy():
    """Initialise spaCy"""
    try:
        import spacy
        nlp = spacy.load("fr_core_news_sm")
        logger.info("spaCy initialisé avec succès")
        return nlp
    except Exception as e:
        logger.error(f"Erreur initialisation spaCy: {e}")
        return None

def initialiser_alira():
    """Initialise ALIRA avec son identité mythologique"""
    logger.info("🏛️ Initialisation d'ALIRA...")
    
    nlp = initialiser_spacy()
    
    couche_memoire = CoucheMemoireMySQL()
    couche_validation = CoucheValidationStricte(nlp)
    couche_modeles = CoucheTemplatesStables(nlp)  # Utilisation des templates
    couche_apprentissage = CoucheApprentissageAutomatique(couche_memoire)
    
    orchestration = CoucheOrchestrationRobuste()
    orchestration.connecter_couches(
        memoire=couche_memoire,
        validation=couche_validation,
        apprentissage=couche_apprentissage,
        modeles=couche_modeles
    )
    
    logger.info("✅ ALIRA initialisée avec templates stables")
    
    return {
        'orchestration': orchestration,
        'nlp': nlp,
        'modele_actif': couche_modeles.modele_charge
    }

# ---------------------------------------------------------
# 10. PROGRAMME PRINCIPAL
# ---------------------------------------------------------

def main():
    """Fonction principale d'ALIRA 1.0 Pallas"""
    print(SIGNATURE)
    print(afficher_avec_style(f"🔮 {PROJECT_NAME} - {FULL_NAME}", Couleurs.BLEU, True))
    print(afficher_avec_style(f"🌟 {MYTHOLOGICAL_SUBTITLE}", Couleurs.ORANGE))
    print(afficher_avec_style(f"🏛️ Version {VERSION}", Couleurs.VERT))
    print("=" * 85)
    print("🎯 PRIORITÉ : SAGESSE > NOUVEAUTÉ")
    print("🔧 Templates éprouvés - Stabilité divine")
    print("⚡ Architecture inspirée des mythes")
    print("=" * 85)
    
    if not verifier_et_installer_dependances():
        print("❌ Impossible d'installer les dépendances nécessaires")
        return
    
    print("\n🔧 Configuration du sanctuaire de données...")
    if not MySQLConfig.setup_database():
        print("❌ Échec de la configuration du sanctuaire")
        return
    
    if not MySQLConfig.test_connection():
        print("❌ Impossible de se connecter au sanctuaire")
        return
    
    print("\n🔧 Initialisation de la sagesse artificielle...")
    alira = initialiser_alira()
    
    if not alira or 'orchestration' not in alira:
        print("❌ Échec de l'initialisation. L'oracle ne peut pas démarrer.")
        return
    
    stats = alira['orchestration'].get_statistiques()
    
    print("\n" + "=" * 85)
    print(f"🎯 {stats}")
    print("💬 Processus sacré en 6 étapes :")
    print("1. 📜 Mémoire ancestrale (prioritaire)")
    print("2. 🔧 Préparation de la question")  
    print("3. 🏺 Templates avec réponses stables")
    print("4. 🌐 Sagesse Wikipedia (recherche)")
    print("5. 📚 Base connaissances (fallback)")
    print("6. 🌱 Apprentissage divin (qualité)")
    print("🔍 Debug: active/désactive avec 'debug'")
    print("📖 Commandes: apprends que, corrige, oublie, statistiques, aide")
    print("=" * 85)
    print("💡 Posez vos questions ou apprenez-moi en disant:")
    print("   \"apprends que [question] est [réponse]\"")
    print("=" * 85)
    
    while True:
        try:
            entree = input("\n🧑 Vous: ").strip()
            
            if not entree:
                continue
                
            if entree.lower() in ['quitter', 'exit', 'au revoir', 'stop', 'quit', 'goodbye']:
                print("🏛️ ALIRA: Que les dieux vous protègent ! À bientôt ! 👋")
                break
            
            if entree.lower() in ['statistiques', 'stats', 'statistique']:
                stats = alira['orchestration'].get_statistiques()
                print(f"🏛️ ALIRA: {stats}")
                continue
            
            if entree.lower() in ['aide', 'help', '?']:
                print(afficher_avec_style("🏛️ ALIRA: Commandes disponibles:", Couleurs.BLEU, True))
                print("  • 'apprends que [question] est [réponse]' - Pour m'enseigner")
                print("  • 'corrige [ancienne question] en [nouvelle réponse]' - Pour corriger")
                print("  • 'oublie [question]' - Pour supprimer une connaissance")
                print("  • 'statistiques' - Voir mon état actuel")
                print("  • 'debug' - Activer/désactiver le mode debug")
                print("  • 'quitter' - Terminer notre conversation")
                continue
            
            if entree.lower() == 'debug':
                alira['orchestration'].toggle_debug()
                continue
            
            # Gestion de l'apprentissage manuel
            if entree.lower().startswith('apprends que'):
                try:
                    parts = entree.split('est', 1)
                    if len(parts) == 2:
                        question = parts[0].replace('apprends que', '').strip()
                        reponse = parts[1].strip()
                        if question and reponse:
                            alira['orchestration'].couches['memoire'].sauvegarder_connaissance(question, reponse)
                            print("🏛️ ALIRA: 📚 Sagesse enregistrée ! Merci de m'enseigner.")
                        else:
                            print("🏛️ ALIRA: Format: apprends que [question] est [réponse]")
                    else:
                        print("🏛️ ALIRA: Format: apprends que [question] est [réponse]")
                except Exception as e:
                    print(f"🏛️ ALIRA: Erreur d'apprentissage: {e}")
                continue
            
            reponse = alira['orchestration'].traiter_question(entree)
            print(f"🏛️ ALIRA: {reponse}")
            
        except KeyboardInterrupt:
            print("\n\n🏛️ ALIRA: Interruption divine détectée. Au revoir !")
            break
        except Exception as e:
            print(f"🏛️ ALIRA: Par les dieux ! Une erreur s'est produite: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        print("💡 Essayez de réinstaller les dépendances:")
        print("   pip install spacy mysql-connector-python python-dotenv requests torch transformers")
        print("   python -m spacy download fr_core_news_sm")
    finally:
        print(f"\nMerci d'avoir consulté l'oracle {PROJECT_NAME} {VERSION} !")
