# config/settings.py
import os
import dotenv

dotenv.load_dotenv()

PROJECT_NAME = "ALIRA"
FULL_NAME = "Accompagnante Libre à Interaction et Réflexion Assistée"
VERSION = "1.0"

# Configuration MySQL
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'database': os.getenv('MYSQL_DATABASE', 'chatbot_db'),
    'user': os.getenv('MYSQL_USER', 'MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD', 'MYSQL_PASSWORD'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True
}

# Paramètres d'apprentissage
LEARNING_CONFIG = {
    'seuil_autonomie': 50,
    'phase_bebe_active': True,
    'timeout_wikipedia': 5,
    'timeout_connexion': 3
}
