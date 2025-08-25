# config/database.py
import mysql.connector
from mysql.connector import Error
from .settings import MYSQL_CONFIG
from utils.logger import logger

class DatabaseConfig:
    @staticmethod
    def get_connection_config():
        return MYSQL_CONFIG
    
    @staticmethod
    def test_connection():
        try:
            config = DatabaseConfig.get_connection_config()
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
        try:
            config = DatabaseConfig.get_connection_config()
            database_name = config.pop('database')
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            # Créer la base de données
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {database_name}")
            
            # Tables (le code reste le même que dans la version originale)
            # ... [code des tables]
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info("Base de données MySQL configurée avec succès")
            return True
            
        except Error as e:
            logger.error(f"Erreur configuration MySQL: {e}")
            return False