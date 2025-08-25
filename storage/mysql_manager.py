# storage/mysql_manager.py
import mysql.connector
from mysql.connector import Error
import json
from config.database import DatabaseConfig
from utils.logger import logger

class MySQLManager:
    def __init__(self):
        self.connection = self.get_connection()
    
    def get_connection(self):
        try:
            config = DatabaseConfig.get_connection_config()
            connection = mysql.connector.connect(**config)
            return connection
        except Error as e:
            logger.error(f"Erreur connexion MySQL: {e}")
            return None
    
    def executer_requete(self, query, params=None, fetchone=False, fetchall=False):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            else:
                result = None
            
            if not query.strip().upper().startswith('SELECT'):
                self.connection.commit()
            
            cursor.close()
            return result
            
        except Error as e:
            logger.error(f"Erreur requête MySQL: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def sauvegarder_connaissance(self, question_normalisee, reponse, variations, source="manuelle"):
        try:
            variations_json = json.dumps(variations, ensure_ascii=False)
            
            if source == "auto_wikipedia":
                reponse = f"📚 {reponse}"
            elif source == "auto_ai":
                reponse = f"🤖 {reponse}"
            
            query = """
            INSERT INTO chatbot_memory (question_normalized, response, variations, learn_count)
            VALUES (%s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE 
                response = VALUES(response),
                variations = VALUES(variations),
                learn_count = learn_count + 1
            """
            
            result = self.executer_requete(query, (question_normalisee, reponse, variations_json))
            return result is not None
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde connaissance: {e}")
            return False
    
    def get_connaissances_similaires(self, phrase, similarite_min=0.7):
        try:
            query = """
            SELECT question_normalized, response, 
                   LEVENSHTEIN(question_normalized, %s) as distance
            FROM chatbot_memory 
            WHERE question_normalized LIKE %s
            ORDER BY distance ASC
            LIMIT 5
            """
            
            pattern = f"%{phrase}%"
            result = self.executer_requete(query, (phrase, pattern), fetchall=True)
            return result or []
            
        except Error as e:
            logger.error(f"Erreur recherche connaissances: {e}")
            return []
    
    def __del__(self):
        if hasattr(self, 'connection') and self.connection and self.connection.is_connected():
            self.connection.close()