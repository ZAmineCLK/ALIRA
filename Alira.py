#!/usr/bin/env python3
"""
ALIRA 1.0 PALLAS - Accompagnante Libre à Interaction et Réflexion Assistée
Version avec compréhension linguistique avancée
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
# CONFIGURATION GLOBALE
# ---------------------------------------------------------
PROJECT_NAME = "ALIRA"
FULL_NAME = "Accompagnante Libre à Interaction et Réflexion Assistée"
VERSION = "1.0 Pallas Linguistique"

# Signature ASCII artistique
SIGNATURE = r"""
 ________  ___       ___  ________  ________     
|\   __  \|\  \     |\  \|\   __  \|\   __  \    
\ \  \|\  \ \  \    \ \  \ \  \|\  \ \  \|\  \   
 \ \   __  \ \  \    \ \  \ \   _  _\ \   __  \  
  \ \  \ \  \ \  \____\ \  \ \  \\  \\ \  \ \  \ 
   \ \__\ \__\ \_______\ \__\ \__\\ _\\ \__\ \__\
    \|__|\|__|\|_______|\|__|\|__|\|__|\|__|\|__|
"""

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
    def get_connection():
        """Établit une connexion MySQL"""
        try:
            config = MySQLConfig.get_connection_config()
            connection = mysql.connector.connect(**config)
            if connection.is_connected():
                return connection
        except Error as e:
            logger.error(f"Erreur de connexion MySQL: {e}")
            return None
    
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
            
            # Table principale des connaissances
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
            
            # Table d'historique des conversations
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
            
            # Table des statistiques
            create_stats_query = """
            CREATE TABLE IF NOT EXISTS learning_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stat_key VARCHAR(50) NOT NULL UNIQUE,
                stat_value INT DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_stats_query)
            
            # Table des concepts sémantiques
            create_semantic_query = """
            CREATE TABLE IF NOT EXISTS concepts_semantiques (
                id INT AUTO_INCREMENT PRIMARY KEY,
                concept_principal VARCHAR(100) NOT NULL,
                synonyms JSON,
                categories JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_concept (concept_principal)
            ) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_semantic_query)
            
            # Table des relations sémantiques
            create_relations_query = """
            CREATE TABLE IF NOT EXISTS relations_semantiques (
                id INT AUTO_INCREMENT PRIMARY KEY,
                concept_source VARCHAR(100) NOT NULL,
                relation_type VARCHAR(50) NOT NULL,
                concept_cible VARCHAR(100) NOT NULL,
                force_relation FLOAT DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_relation (concept_source, relation_type, concept_cible)
            ) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_relations_query)
            
            # Table des variations avec contexte
            create_variations_query = """
            CREATE TABLE IF NOT EXISTS variations_contexte (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_id INT NOT NULL,
                variation TEXT NOT NULL,
                type_contexte VARCHAR(50),
                confidence FLOAT DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES chatbot_memory(id),
                INDEX idx_variation (variation(100)),
                INDEX idx_type_contexte (type_contexte)
            ) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_variations_query)
            
            # Données initiales des statistiques
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
# 4. COMPRÉHENSION LINGUISTIQUE AVANCÉE
# ---------------------------------------------------------

class ComprehenseurLinguistique:
    """Analyse syntaxique et sémantique des phrases pour une vraie compréhension"""
    
    def __init__(self, nlp):
        self.nlp = nlp
        self.mots_interrogatifs = {
            'quoi', 'qui', 'comment', 'pourquoi', 'quand', 'où', 'combien',
            'quel', 'quelle', 'quels', 'quelles', 'est-ce que', 'qu\'est-ce que'
        }
        self.verbes_connaissance = {
            'savoir', 'connaître', 'apprendre', 'enseigner', 'expliquer',
            'définir', 'dire', 'signifier', 'vouloir savoir'
        }
    
    def analyser_structure_phrase(self, phrase):
        """Analyse syntaxique approfondie de la phrase"""
        if not phrase or not self.nlp:
            return None
        
        doc = self.nlp(phrase.lower())
        analyse = {
            'phrase_originale': phrase,
            'mots_cles': [],
            'type_phrase': self._determiner_type_phrase(doc),
            'intention': self._detecter_intention(doc),
            'sujet_principal': self._extraire_sujet(doc),
            'action_principale': self._extraire_action(doc),
            'complement_principal': self._extraire_complement(doc),
            'est_question': any(token.text in self.mots_interrogatifs for token in doc),
            'est_demande_connaissance': any(token.lemma_ in self.verbes_connaissance for token in doc)
        }
        
        # Extraction des mots-clés significatifs
        for token in doc:
            if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'PROPN'] and not token.is_stop:
                analyse['mots_cles'].append({
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'tag': token.tag_
                })
        
        return analyse
    
    def _determiner_type_phrase(self, doc):
        """Détermine le type de phrase"""
        if any(token.text in self.mots_interrogatifs for token in doc):
            return 'question'
        elif any(token.tag_ == 'VERB' and token.morph.get('Mood') == ['Imp'] for token in doc):
            return 'imperatif'
        else:
            return 'declaration'
    
    def _detecter_intention(self, doc):
        """Détecte l'intention derrière la phrase"""
        texte = doc.text.lower()
        
        if any(mot in texte for mot in ['quoi', 'qu\'est', 'défini', 'signifi']):
            return 'demande_definition'
        elif any(mot in texte for mot in ['qui', 'personne']):
            return 'demande_identite'
        elif any(mot in texte for mot in ['comment', 'faire']):
            return 'demande_procedure'
        elif any(mot in texte for mot in ['pourquoi', 'cause', 'raison']):
            return 'demande_explication'
        elif any(mot in texte for mot in ['quand', 'heure', 'temps']):
            return 'demande_temps'
        elif any(mot in texte for mot in ['où', 'lieu', 'endroit']):
            return 'demande_localisation'
        else:
            return 'demande_generale'
    
    def _extraire_sujet(self, doc):
        """Extrait le sujet principal de la phrase"""
        for token in doc:
            if token.dep_ in ['nsubj', 'nsubj:pass'] and token.pos_ in ['NOUN', 'PROPN', 'PRON']:
                return {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_
                }
        return None
    
    def _extraire_action(self, doc):
        """Extrait l'action principale"""
        for token in doc:
            if token.pos_ == 'VERB' and token.dep_ in ['ROOT', 'conj']:
                return {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'tense': token.morph.get('Tense', ['present'])[0]
                }
        return None
    
    def _extraire_complement(self, doc):
        """Extrait le complément principal"""
        for token in doc:
            if token.dep_ in ['obj', 'obl', 'attr'] and token.pos_ in ['NOUN', 'PROPN']:
                return {
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_
                }
        return None
    
    def normaliser_phrase(self, phrase):
        """Normalisation avancée basée sur l'analyse linguistique"""
        analyse = self.analyser_structure_phrase(phrase)
        if not analyse:
            return phrase.lower()
        
        # Construction d'une forme normalisée
        elements = []
        
        if analyse['sujet_principal']:
            elements.append(analyse['sujet_principal']['lemma'])
        
        if analyse['action_principale']:
            elements.append(analyse['action_principale']['lemma'])
        
        if analyse['complement_principal']:
            elements.append(analyse['complement_principal']['lemma'])
        
        # Ajout des mots-clés supplémentaires
        for mot_cle in analyse['mots_cles']:
            if mot_cle['lemma'] not in elements:
                elements.append(mot_cle['lemma'])
        
        phrase_normalisee = ' '.join(elements)
        return phrase_normalisee if phrase_normalisee else phrase.lower()
    
    def generer_variations_semantiques(self, phrase):
        """Génère des variations basées sur la sémantique"""
        analyse = self.analyser_structure_phrase(phrase)
        if not analyse:
            return [phrase.lower()]
        
        variations = set()
        variations.add(phrase.lower())
        
        # Variations basées sur l'intention
        sujet = analyse['sujet_principal']['lemma'] if analyse['sujet_principal'] else ''
        
        if analyse['intention'] == 'demande_definition':
            variations.update([
                f"définition {sujet}",
                f"qu'est-ce que {sujet}",
                f"signification {sujet}"
            ])
        
        # Variations de formulation
        formulations = [
            f"explique moi {sujet}",
            f"dis moi {sujet}",
            f"c'est quoi {sujet}",
            f"je veux savoir {sujet}"
        ]
        
        variations.update(formulations)
        return list(variations)

# ---------------------------------------------------------
# 5. MÉMOIRE SÉMANTIQUE AVANCÉE
# ---------------------------------------------------------

class MemoireSemantique:
    """Mémoire qui comprend le sens des phrases, pas juste les mots"""
    
    def __init__(self, connection, nlp):
        self.connection = connection
        self.comprehenseur = ComprehenseurLinguistique(nlp)
    
    def sauvegarder_connaissance_semantique(self, question, reponse):
        """Sauvegarde avec analyse sémantique complète"""
        try:
            # Analyse sémantique de la question
            analyse = self.comprehenseur.analyser_structure_phrase(question)
            if not analyse:
                return False
            
            # Extraction du concept principal
            concept_principal = self._extraire_concept_principal(analyse)
            
            # Sauvegarde dans la mémoire traditionnelle
            question_normalisee = self.comprehenseur.normaliser_phrase(question)
            
            cursor = self.connection.cursor()
            cursor.execute("""
            INSERT INTO chatbot_memory (question_normalized, response, learn_count)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE 
                response = VALUES(response),
                learn_count = learn_count + 1
            """, (question_normalisee, reponse))
            
            # Récupération de l'ID
            cursor.execute("SELECT id FROM chatbot_memory WHERE question_normalized = %s", 
                          (question_normalisee,))
            result = cursor.fetchone()
            if result:
                question_id = result[0]
                
                # Sauvegarde des variations sémantiques
                variations = self.comprehenseur.generer_variations_semantiques(question)
                for variation in variations:
                    cursor.execute("""
                    INSERT INTO variations_contexte (question_id, variation, type_contexte, confidence)
                    VALUES (%s, %s, 'semantique', 0.9)
                    ON DUPLICATE KEY UPDATE confidence = VALUES(confidence)
                    """, (question_id, variation))
            
            # Sauvegarde sémantique
            if concept_principal:
                self._sauvegarder_concept(concept_principal, analyse, reponse)
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Erreur sauvegarde sémantique: {e}")
            return False
    
    def _extraire_concept_principal(self, analyse):
        """Extrait le concept principal de l'analyse"""
        if analyse['sujet_principal']:
            return analyse['sujet_principal']['lemma']
        elif analyse['complement_principal']:
            return analyse['complement_principal']['lemma']
        elif analyse['mots_cles']:
            return analyse['mots_cles'][0]['lemma']
        return None
    
    def _sauvegarder_concept(self, concept, analyse, reponse):
        """Sauvegarde le concept sémantique"""
        try:
            cursor = self.connection.cursor()
            
            # Sauvegarde du concept principal
            synonyms = [mot['lemma'] for mot in analyse['mots_cles'] if mot['lemma'] != concept]
            
            cursor.execute("""
            INSERT INTO concepts_semantiques (concept_principal, synonyms)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE synonyms = JSON_MERGE_PRESERVE(synonyms, VALUES(synonyms))
            """, (concept, json.dumps(synonyms)))
            
            # Sauvegarde des relations sémantiques
            if analyse['action_principale']:
                cursor.execute("""
                INSERT INTO relations_semantiques (concept_source, relation_type, concept_cible)
                VALUES (%s, 'action', %s)
                ON DUPLICATE KEY UPDATE force_relation = force_relation + 0.1
                """, (concept, analyse['action_principale']['lemma']))
            
            self.connection.commit()
            cursor.close()
            
        except Error as e:
            logger.error(f"Erreur sauvegarde concept: {e}")
    
    def rechercher_semantiquement(self, question):
        """Recherche basée sur la sémantique, pas juste les mots"""
        analyse = self.comprehenseur.analyser_structure_phrase(question)
        if not analyse:
            return None
        
        concept_recherche = self._extraire_concept_principal(analyse)
        if not concept_recherche:
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Recherche par concept principal
            cursor.execute("""
            SELECT cm.response 
            FROM concepts_semantiques cs
            JOIN chatbot_memory cm ON cs.concept_principal = cm.question_normalized
            WHERE cs.concept_principal = %s 
            OR JSON_CONTAINS(cs.synonyms, %s)
            LIMIT 1
            """, (concept_recherche, json.dumps(concept_recherche)))
            
            result = cursor.fetchone()
            if result:
                cursor.close()
                return result['response']
            
            # Recherche par relations sémantiques
            cursor.execute("""
            SELECT cm.response 
            FROM relations_semantiques rs
            JOIN concepts_semantiques cs ON rs.concept_cible = cs.concept_principal
            JOIN chatbot_memory cm ON cs.concept_principal = cm.question_normalized
            WHERE rs.concept_source = %s 
            AND rs.force_relation > 0.5
            ORDER BY rs.force_relation DESC
            LIMIT 1
            """, (concept_recherche,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result['response'] if result else None
            
        except Error as e:
            logger.error(f"Erreur recherche sémantique: {e}")
            return None

# ---------------------------------------------------------
# 6. COUCHE MÉMOIRE PERSISTANTE
# ---------------------------------------------------------

class CoucheMemoireMySQL:
    """Gère la mémoire persistante avec MySQL"""
    
    def __init__(self, nlp=None):
        self.connection = MySQLConfig.get_connection()
        self.nlp = nlp
        self.memoire_semantique = MemoireSemantique(self.connection, nlp) if nlp else None
    
    def consulter_memoire(self, question):
        """Consulte la mémoire pour une question"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = MySQLConfig.get_connection()
                
            question_normalisee = normaliser_question(question)
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, response FROM chatbot_memory WHERE question_normalized = %s", 
                          (question_normalisee,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                self._incrementer_utilisation(result['id'])
                return result['response']
            
            # Recherche sémantique si disponible
            if self.memoire_semantique:
                reponse_semantique = self.memoire_semantique.rechercher_semantiquement(question)
                if reponse_semantique:
                    return reponse_semantique
                    
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
                self.connection = MySQLConfig.get_connection()
                
            # Utilisation de la mémoire sémantique si disponible
            if self.memoire_semantique:
                return self.memoire_semantique.sauvegarder_connaissance_semantique(question, reponse)
            else:
                # Fallback à la méthode traditionnelle
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
# 7. COUCHE VALIDATION (AMÉLIORÉE)
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
        if len(reponse) < 15:
            logger.warning("Réponse trop courte")
            return False
        
        reponse_lower = reponse.lower()
        
        # Rejeter les réponses incomplètes
        if reponse.strip().endswith(('est :', 'signifie :', 'est : ', 'signifie : ', ':')):
            logger.warning("Réponse incomplète")
            return False
        
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
        
        # Vérification de cohérence basique
        return self.est_pertinente(reponse, question_originale)
    
    def est_pertinente(self, reponse, question):
        """Vérifie la pertinence sémantique"""
        if not question or not reponse:
            return False
        
        # Vérifier que la réponse n'est pas une demande d'apprentissage
        if "enseign" in reponse.lower() or "apprend" in reponse.lower():
            return False
        
        mots_question = set(question.lower().split())
        mots_reponse = set(reponse.lower().split())
        
        stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'est', 'que', 'quoi', 'c\'est'}
        
        mots_communs = mots_question.intersection(mots_reponse) - stop_words
        return len(mots_communs) > 0

# ---------------------------------------------------------
# 8. COUCHE TEMPLATES STABLES (CORRIGÉE)
# ---------------------------------------------------------

class CoucheTemplatesStables:
    """Gère des templates avec réponses claires et directes"""
    
    def __init__(self, nlp=None):
        self.nlp = nlp
        self.modele_charge = True
        self._initialiser_templates()
    
    def _initialiser_templates(self):
        """Initialise les templates de réponse complets"""
        self.templates = {
            'definition': [
                "{} est {}",
                "La définition de {} est : {}",
                "{} se définit comme {}",
                "En termes simples, {} signifie {}",
                "{} correspond à {}"
            ],
            'biographie': [
                "{} est {}",
                "Concernant {} : {}",
                "Voici ce qu'il faut savoir sur {} : {}",
                "{} peut être décrit comme {}"
            ],
            'procedure': [
                "Pour {} : {}",
                "La procédure pour {} : {}",
                "Voici comment {} : {}",
                "Les étapes pour {} : {}"
            ]
        }
        
        # Base de connaissances complète avec réponses terminées
        self.connaissances_claires = {
            'nymphes': "des divinités mineures de la nature dans la mythologie grecque, souvent associées aux forêts, montagnes et cours d'eau",
            'divine': "qui relève de la nature des dieux, de l'essence sacrée et transcendante",
            'nature': "l'ensemble des phénomènes et êtres qui constituent l'univers, indépendamment de l'action humaine",
            'mythologie': "l'étude des mythes et des récits légendaires qui fondent les croyances et traditions des civilisations",
            'philosophie': "la recherche de la sagesse et la réflexion sur les questions fondamentales de l'existence",
            'sagesse': "la connaissance approfondie et le jugement éclairé qui permettent de bien conduire sa vie",
            'culasse': "une pièce importante du moteur qui ferme la chambre de combustion et supporte les soupapes",
            'moteur': "un dispositif qui transforme une énergie en mouvement mécanique",
            'ordinateur': "une machine électronique qui traite des données selon des instructions programmées",
            'internet': "un réseau mondial qui connecte des millions d'ordinateurs et permet l'échange d'informations",
            'intelligence artificielle': "un domaine de l'informatique qui cherche à créer des machines capables de simuler l'intelligence humaine",
            'voiture': "un véhicule motorisé à roues utilisé pour le transport personnel",
            'maison': "un bâtiment destiné à l'habitation",
            'école': "un établissement où l'on dispense un enseignement collective",
            'travail': "une activité productive qui permet de subvenir à ses besoins",
            'amour': "un sentiment d'affection intense envers quelqu'un ou quelque chose",
            'amitié': "une relation affective entre deux personnes qui partagent des affinités",
            'famille': "un groupe de personnes liées par le sang, le mariage ou l'adoption",
            'ville': "une agglomération humaine importante avec une administration propre",
            'pays': "un territoire habité par une nation et doté d'un gouvernement",
            'tom cruise': "un acteur et producteur de cinéma américain né en 1962, connu pour ses rôles dans des films comme 'Top Gun' et 'Mission Impossible'",
            'tom cruse': "probablement une référence à Tom Cruise, acteur et producteur de cinéma américain né en 1962",
            'bébé': "un jeune enfant en bas âge, généralement de la naissance à 2 ans",
            'bebe': "un jeune enfant en bas âge, généralement de la naissance à 2 ans",
            'clear': "un terme anglais signifiant 'clair' ou 'nettoyer'. En informatique, cela peut vouloir dire effacer l'écran"
        }
    
    def _extraire_terme_principal(self, question):
        """Extrait le terme principal de la question"""
        question_lower = question.lower()
        
        # Supprimer les mots interrogatifs
        motifs_a_supprimer = [
            r'que veut dire', r'qu\'est ce que', r'qu\'est-ce que', 
            r'c\'est quoi', r'définition de', r'explique moi', r'c\'est quoi une',
            r'c\'est quoi un', r'qu\'est ce qu\'une', r'qu\'est-ce qu\'une'
        ]
        
        terme = question_lower
        for motif in motifs_a_supprimer:
            terme = re.sub(motif, '', terme, flags=re.IGNORECASE)
        
        terme = re.sub(r'[?¿]', '', terme).strip()
        return terme.capitalize() if terme else question
    
    def generer_reponse_fiable(self, question):
        """Génération via templates avec réponses complètes"""
        question_lower = question.lower()
        terme = self._extraire_terme_principal(question)
        terme_lower = terme.lower()
        
        # D'abord vérifier si on a une connaissance complète
        if terme_lower in self.connaissances_claires:
            template = random.choice(self.templates['definition'])
            return template.format(terme, self.connaissances_claires[terme_lower])
        
        # Ensuite utiliser les templates génériques avec fallback
        if any(mot in question_lower for mot in ['quoi', 'qu\'est', 'défini', 'c\'est quoi', 'que veut dire', 'définition', 'explique']):
            template = random.choice(self.templates['definition'])
            return template.format(terme, "un concept que je ne connais pas encore. Pouvez-vous me l'expliquer ?")
        
        elif any(mot in question_lower for mot in ['qui', 'personne', 'histoire de']):
            template = random.choice(self.templates['biographie'])
            return template.format(terme, "une personne que je ne connais pas encore. Pouvez-vous me la présenter ?")
        
        elif any(mot in question_lower for mot in ['comment', 'faire', 'procédé']):
            template = random.choice(self.templates['procedure'])
            return template.format(terme, "un processus que je ne maîtrise pas encore. Pouvez-vous me l'enseigner ?")
        
        else:
            return self._reponse_fallback(question)
    
    def _reponse_fallback(self, question):
        """Réponses de fallback claires et utiles"""
        return "Je ne possède pas encore cette information. Pourriez-vous me l'enseigner en disant : 'apprends que [question] est [réponse]' ?"

# ---------------------------------------------------------
# 9. COUCHE APPRENTISSAGE AUTOMATIQUE
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
# 10. ORCHESTRATION LINGUISTIQUE
# ---------------------------------------------------------

class OrchestrationLinguistique:
    """Orchestration avec vraie compréhension linguistique"""
    
    def __init__(self, nlp):
        self.nlp = nlp
        self.comprehenseur = ComprehenseurLinguistique(nlp)
        self.memoire_semantique = None
        self.debug_mode = True
    
    def connecter_memoire_semantique(self, connection):
        """Connecte la mémoire sémantique"""
        self.memoire_semantique = MemoireSemantique(connection, self.nlp)
    
    def _rechercher_wikipedia(self, question):
        """Recherche sur Wikipedia"""
        try:
            question_propre = nettoyer_question_pour_recherche(question)
            if not question_propre or len(question_propre) < 3:
                return None
            
            url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{quote(question_propre)}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data and data['extract']:
                    extract = data['extract'].strip()
                    if extract and len(extract) > 30:
                        return extract[:350] + "..." if len(extract) > 350 else extract
            
            return None
                
        except Exception as e:
            if self.debug_mode:
                print(f"❓ [DEBUG] Erreur Wikipedia: {e}")
            return None
    
    def _rechercher_base_connaissances(self, question):
        """Recherche dans la base de connaissances intégrée"""
        connaissances_base = {
            'maman': "une figure parentale féminine qui donne naissance et élève ses enfants avec amour",
            'paris': "la capitale de la France, située au nord du pays sur la Seine",
            'france': "un pays d'Europe occidentale, connu pour sa culture, son histoire et sa gastronomie",
            'intelligence artificielle': "un domaine de l'informatique qui développe des systèmes capables de performances intellectuelles",
            'bébé': "un jeune enfant en bas âge, généralement de la naissance à 2 ans",
            'papa': "une figure parentale masculine qui participe à l'éducation des enfants",
            'famille': "un groupe de personnes liées par le sang, le mariage ou l'adoption",
            'ordinateur': "une machine électronique qui traite des données selon des instructions programmées",
            'internet': "un réseau mondial qui connecte des millions d'appareils et permet l'échange d'informations",
            'apprendre': "le processus d'acquisition de connaissances ou de compétences",
            'mythologie': "l'étude des mythes et récits traditionnels des différentes cultures",
            'grèce': "un pays d'Europe du Sud, berceau de la démocratie et de la philosophie occidentale",
            'athéna': "déesse de la sagesse et de la guerre stratégique dans la mythologie grecque",
            'zeus': "le roi des dieux dans la mythologie grecque, maître du tonnerre",
            'déesse': "une divinité féminine dans les différentes mythologies",
            'oracle': "une personne ou un lieu qui transmettait des prophéties dans l'antiquité",
            'divine': "qui appartient à la nature des dieux ou qui est d'une perfection exceptionnelle",
            'nature': "l'ensemble des phénomènes et êtres qui constituent l'univers physique",
            'culasse': "une pièce mécanique qui ferme la chambre de combustion dans un moteur",
            'voiture': "un véhicule motorisé à roues utilisé pour le transport personnel",
            'tom cruise': "un acteur et producteur de cinéma américain né en 1962, connu pour ses rôles dans des films comme 'Top Gun' et 'Mission Impossible'",
            'bebe': "un jeune enfant en bas âge, généralement de la naissance à 2 ans"
        }
        
        question_lower = question.lower()
        for mot, reponse in connaissances_base.items():
            if mot in question_lower:
                return reponse
        
        return None
    
    def _generer_reponse_adaptee(self, analyse):
        """Génère une réponse adaptée à l'analyse linguistique"""
        intention = analyse['intention']
        concept = analyse['sujet_principal']['lemma'] if analyse['sujet_principal'] else "cela"
        
        reponses_adaptees = {
            'demande_definition': 
                f"Je ne connais pas encore la définition de '{concept}'. Pouvez-vous me l'enseigner ?",
            'demande_identite': 
                f"Je n'ai pas d'information sur '{concept}'. Pourriez-vous me le présenter ?",
            'demande_procedure': 
                f"Je ne sais pas encore comment procéder pour '{concept}'. Pouvez-vous m'expliquer ?",
            'demande_explication': 
                f"Je n'ai pas l'explication pour '{concept}'. Pourriez-vous me l'apprendre ?",
            'demande_temps': 
                f"Je ne peux pas encore vous dire quand pour '{concept}'. J'ai besoin d'apprendre cette information.",
            'demande_localisation': 
                f"Je ne connais pas la localisation de '{concept}'. Pouvez-vous me l'indiquer ?",
            'demande_generale': 
                f"Je n'ai pas encore appris à propos de '{concept}'. Pouvez-vous m'enseigner cela ?"
        }
        
        return reponses_adaptees.get(intention, 
            "Je ne possède pas encore cette connaissance. Pourriez-vous me l'enseigner ?")
    
    def traiter_question(self, question):
        """Traite la question avec compréhension linguistique"""
        if not question:
            return "Veuillez poser une question."
        
        # Analyse linguistique complète
        analyse = self.comprehenseur.analyser_structure_phrase(question)
        
        if not analyse:
            return "Je n'ai pas bien compris votre question. Pouvez-vous reformuler ?"
        
        if self.debug_mode:
            print(f"🔍 [DEBUG] Analyse: {analyse['intention']} - {analyse['sujet_principal']}")
        
        # 1. Recherche sémantique avancée
        if self.memoire_semantique:
            reponse_semantique = self.memoire_semantique.rechercher_semantiquement(question)
            if reponse_semantique:
                if self.debug_mode:
                    print(f"✅ [DEBUG] Trouvé par sémantique")
                return reponse_semantique
        
        # 2. Recherche par variations sémantiques
        variations = self.comprehenseur.generer_variations_semantiques(question)
        for variation in variations:
            reponse_variation = self.memoire_semantique.rechercher_semantiquement(variation)
            if reponse_variation:
                if self.debug_mode:
                    print(f"✅ [DEBUG] Trouvé par variation: {variation}")
                return reponse_variation
        
        # 3. Recherche Wikipedia
        if reponse_wiki := self._rechercher_wikipedia(question):
            if self.debug_mode:
                print(f"🌐 [DEBUG] Trouvé sur Wikipedia")
            return reponse_wiki
        
        # 4. Base de connaissances interne
        if reponse_base := self._rechercher_base_connaissances(question):
            if self.debug_mode:
                print(f"📚 [DEBUG] Trouvé en base interne")
            return reponse_base
        
        # 5. Réponse adaptée au type de phrase
        return self._generer_reponse_adaptee(analyse)
    
    def toggle_debug(self):
        """Active/désactive le mode debug"""
        self.debug_mode = not self.debug_mode
        statut = "ACTIVÉ" if self.debug_mode else "DÉSACTIVÉ"
        print(f"🔍 Mode debug {statut}")
        return self.debug_mode

# ---------------------------------------------------------
# 11. INITIALISATION DES COMPOSANTS
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
    """Initialise ALIRA avec compréhension linguistique"""
    logger.info("🏛️ Initialisation d'ALIRA avec compréhension linguistique...")
    
    nlp = initialiser_spacy()
    
    # Initialisation des composants
    couche_memoire = CoucheMemoireMySQL(nlp)
    couche_validation = CoucheValidationStricte(nlp)
    couche_modeles = CoucheTemplatesStables(nlp)
    couche_apprentissage = CoucheApprentissageAutomatique(couche_memoire)
    
    # Orchestration linguistique
    orchestration = OrchestrationLinguistique(nlp)
    orchestration.connecter_memoire_semantique(couche_memoire.connection)
    
    logger.info("✅ ALIRA initialisée avec compréhension linguistique")
    
    return {
        'orchestration': orchestration,
        'memoire': couche_memoire,
        'validation': couche_validation,
        'modeles': couche_modeles,
        'apprentissage': couche_apprentissage,
        'nlp': nlp
    }

# ---------------------------------------------------------
# 12. PROGRAMME PRINCIPAL
# ---------------------------------------------------------

def main():
    """Fonction principale d'ALIRA 1.0 Pallas Linguistique"""
    print(SIGNATURE)
    print(afficher_avec_style(f"🔮 {PROJECT_NAME} - {FULL_NAME}", Couleurs.BLEU, True))
    print(afficher_avec_style(f"🏛️ Version {VERSION}", Couleurs.VERT))
    print("=" * 85)
    print("🎯 PRIORITÉ : COMPRÉHENSION LINGUISTIQUE AVANCÉE")
    print("🧠 Analyse syntaxique et sémantique")
    print("🌍 Compréhension réelle des phrases")
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
    
    print("\n🔧 Initialisation de l'assistant...")
    alira = initialiser_alira()
    
    if not alira:
        print("❌ Échec de l'initialisation. L'assistant ne peut pas démarrer.")
        return
    
    print("\n" + "=" * 85)
    print("💬 Processus de compréhension linguistique :")
    print("1. 🔍 Analyse syntaxique et sémantique")
    print("2. 🧠 Extraction des concepts principaux")
    print("3. 🌐 Recherche par intention")
    print("4. 📚 Base connaissances contextuelle")
    print("5. 🎯 Réponse adaptée au type de question")
    print("🔍 Debug: active/désactive avec 'debug'")
    print("📖 Commandes: apprends que, corrige, oublie, statistiques, aide")
    print("=" * 85)
    print("💡 Posez vos questions naturellement :")
    print("   \"Qu'est-ce qu'un ordinateur ?\"")
    print("   \"Explique-moi l'intelligence artificielle\"")
    print("   \"Dis-moi comment fonctionne internet\"")
    print("=" * 85)
    
    while True:
        try:
            entree = input("\n🧑 Vous: ").strip()
            
            if not entree:
                continue
                
            if entree.lower() in ['quitter', 'exit', 'au revoir', 'stop', 'quit', 'goodbye']:
                print("🏛️ ALIRA: Au revoir ! À bientôt ! 👋")
                break
            
            if entree.lower() in ['statistiques', 'stats', 'statistique']:
                nb_connaissances = alira['memoire'].get_nombre_connaissances()
                niveau = alira['memoire'].get_niveau_autonomie()
                print(f"🏛️ ALIRA: 📊 Connaissances: {nb_connaissances} | Niveau: {niveau}")
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
                            alira['memoire'].sauvegarder_connaissance(question, reponse)
                            print("🏛️ ALIRA: ✅ Connaissance enregistrée ! Merci de m'enseigner.")
                        else:
                            print("🏛️ ALIRA: ❌ Format: apprends que [question] est [réponse]")
                    else:
                        print("🏛️ ALIRA: ❌ Format: apprends que [question] est [réponse]")
                except Exception as e:
                    print(f"🏛️ ALIRA: ❌ Erreur d'apprentissage: {e}")
                continue
            
            # Traitement avec compréhension linguistique
            reponse = alira['orchestration'].traiter_question(entree)
            print(f"🏛️ ALIRA: {reponse}")
            
        except KeyboardInterrupt:
            print("\n\n🏛️ ALIRA: Interruption détectée. Au revoir !")
            break
        except Exception as e:
            print(f"🏛️ ALIRA: ❌ Une erreur s'est produite: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        print("💡 Essayez de réinstaller les dépendances:")
        print("   pip install spacy mysql-connector-python python-dotenv requests torch transformers")
        print("   python -m spacy download fr_core_news_sm")
    finally:
        print(f"\nMerci d'avoir utilisé {PROJECT_NAME} {VERSION} !")
