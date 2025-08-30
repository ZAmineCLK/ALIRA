#!/usr/bin/env python3
"""
ALIRA - Accompagnante Libre à Interaction et Réflexion Assistée
Point d'entrée principal
"""

import sys
import random
from config.settings import PROJECT_NAME, FULL_NAME, VERSION
from utils.dependencies import verifier_et_installer_dependances, verifier_modele_spacy
from config.database import DatabaseConfig
from core.nlp_processor import initialiser_spacy
from models.chatterbot_wrapper import initialiser_chatterbot
from core.learning_system import SystemeApprentissage
from utils.logger import logger

def afficher_banniere():
    print(f"🤖 {PROJECT_NAME} - {FULL_NAME}")
    print(f"Version {VERSION} - Votre assistante conversationnelle intelligente")
    print("=" * 85)

def initialiser_systeme():
    """Initialise tous les composants du système"""
    logger.info("Initialisation du système...")
    
    # Vérifier les dépendances
    if not verifier_et_installer_dependances():
        logger.error("Impossible d'installer les dépendances nécessaires")
        return None, None, None
    
    # Configuration MySQL
    logger.info("Configuration MySQL...")
    if not DatabaseConfig.setup_database():
        logger.error("Échec de la configuration MySQL")
        return None, None, None
    
    if not DatabaseConfig.test_connection():
        logger.error("Impossible de se connecter à MySQL")
        return None, None, None
    
    # Initialiser les composants
    logger.info("Initialisation des composants...")
    nlp = initialiser_spacy()
    chatbot = initialiser_chatterbot()
    systeme_apprentissage = SystemeApprentissage(nlp)
    
    if nlp is None or chatbot is None or systeme_apprentissage.mysql_manager.connection is None:
        logger.error("Échec de l'initialisation")
        return None, None, None
    
    # Charger le modèle assistant
    logger.info("Chargement du modèle assistant phase bébé...")
    if not systeme_apprentissage.assistant_bebe.charger_modele_assistant():
        logger.warning("Échec du chargement du modèle assistant")
    
    return nlp, chatbot, systeme_apprentissage

def boucle_conversation(nlp, chatbot, systeme_apprentissage):
    """Boucle principale de conversation"""
    est_phase_bebe = systeme_apprentissage.verifier_phase_bebe()
    
    # Aide utilisateur
    print("\n" + "=" * 85)
    if est_phase_bebe:
        print("👶 ALIRA est en PHASE BÉBÉ - Modèle assistant activé")
        print("💡 Je vais apprendre de mes erreurs avec l'aide de mon assistant")
    else:
        print("🎓 ALIRA est en MODE AUTONOME")
    
    print("💬 Processus en 4 étapes activé :")
    print("1. 📚 Mémoire personnelle")
    print("2. 👶 Modèle assistant (phase bébé)" if est_phase_bebe else "2. 🤖 Modèle local")
    print("3. 🌐 Wikipedia")
    print("4. 💬 ChatterBot (fallback)")
    print("📚 Commandes : apprends que, corrige, oublie, statistiques")
    print("=" * 85)
    
    # Boucle de conversation
    while True:
        try:
            entree = input("\n👤 Vous: ").strip()
            
            if not entree:
                continue
                
            if entree.lower() in ['quitter', 'exit', 'au revoir', 'stop', 'quit', 'goodbye']:
                print("👩‍💻 ALIRA: Au revoir ! À bientôt ! 👋")
                break
            
            # Traitement de la phrase
            reponse = systeme_apprentissage.gerer_conversation(nlp, chatbot, entree)
            print(f"👩‍💻 ALIRA: {reponse}")
            
        except KeyboardInterrupt:
            print("\n\n👩‍💻 ALIRA: Interruption détectée. Au revoir !")
            break
        except Exception as e:
            print(f"👩‍💻 ALIRA: Désolée, une erreur s'est produite: {e}")

def main():
    """Fonction principale"""
    afficher_banniere()
    
    try:
        nlp, chatbot, systeme_apprentissage = initialiser_systeme()
        
        if not all([nlp, chatbot, systeme_apprentissage]):
            logger.error("Le système n'a pas pu être initialisé")
            return
        
        # Apprentissage initial
        logger.info("Apprentissage initial des connaissances de base...")
        systeme_apprentissage.apprentissage_initial(chatbot)
        
        # Démarrer la conversation
        boucle_conversation(nlp, chatbot, systeme_apprentissage)
        
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        print("💡 Essayez de réinstaller les dépendances:")
        print("   pip install spacy chatterbot chatterbot-corpus mysql-connector-python python-dotenv requests torch transformers sentence-transformers accelerate")
        print("   python -m spacy download fr_core_news_sm")
    finally:
        print(f"\nMerci d'avoir utilisé {PROJECT_NAME} !")

if __name__ == "__main__":
    main()
