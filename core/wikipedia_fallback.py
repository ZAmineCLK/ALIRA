# core/wikipedia_fallback.py
import requests
from urllib.parse import quote
from utils.logger import logger
from config.settings import LEARNING_CONFIG

class WikipediaFallback:
    def __init__(self):
        self.connexion_verifiee = False
        self.connexion_disponible = False
        self.timeout_connexion = LEARNING_CONFIG['timeout_connexion']
        self.timeout_requete = LEARNING_CONFIG['timeout_wikipedia']
    
    def verifier_connexion_internet(self):
        if self.connexion_verifiee:
            return self.connexion_disponible
            
        logger.info("Vérification de la connexion Internet...")
        try:
            sites_test = [
                "https://www.google.com",
                "https://www.wikipedia.org",
                "https://www.github.com"
            ]
            
            for site in sites_test:
                try:
                    response = requests.get(site, timeout=self.timeout_connexion)
                    if response.status_code == 200:
                        self.connexion_disponible = True
                        break
                except:
                    continue
            
            self.connexion_verifiee = True
            logger.info(f"Connexion Internet: {'Disponible' if self.connexion_disponible else 'Indisponible'}")
            return self.connexion_disponible
            
        except Exception as e:
            logger.error(f"Erreur vérification connexion: {e}")
            self.connexion_disponible = False
            self.connexion_verifiee = True
            return False
    
    def rechercher_wikipedia(self, terme_recherche, langue="fr"):
        if not self.verifier_connexion_internet():
            return None
        
        try:
            url = f"https://{langue}.wikipedia.org/api/rest_v1/page/summary/{quote(terme_recherche)}"
            response = requests.get(url, timeout=self.timeout_requete)
            
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data and data['extract']:
                    return data['extract']
                elif 'description' in data and data['description']:
                    return data['description']
            
            return None
            
        except requests.exceptions.Timeout:
            logger.warning("Timeout lors de la recherche Wikipedia")
            return None
        except Exception as e:
            logger.error(f"Erreur recherche Wikipedia: {e}")
            return None
    
    def extraire_terme_principal(self, question, nlp=None):
        if not question:
            return None
        
        question_propre = re.sub(r'(bonjour|salut|hello|hi|coucou|merci|thank you|thanks|s\'il vous plaît|please)', '', question, flags=re.IGNORECASE)
        question_propre = re.sub(r'(c\'est quoi|qu\'est-ce que|que veut dire|définition de?|explique|quel est|quelle est|what is|what does|define)', '', question_propre, flags=re.IGNORECASE)
        question_propre = re.sub(r'[?¿.,!]', '', question_propre).strip()
        
        if not question_propre:
            return None
        
        if nlp:
            try:
                doc = nlp(question_propre)
                for ent in doc.ents:
                    if ent.label_ in ['LOC', 'GPE', 'ORG', 'PER', 'MISC']:
                        logger.info(f"Entité nommée trouvée: {ent.text} (label: {ent.label_})")
                        return ent.text
                
                noms_propres = []
                for token in doc:
                    if (token.pos_ in ['PROPN', 'NOUN'] and not token.is_stop and len(token.text) > 2):
                        noms_propres.append(token.text)
                
                if noms_propres:
                    return noms_propres[0]
                    
            except Exception as e:
                logger.warning(f"Erreur analyse spaCy: {e}")
        
        mots = question_propre.split()
        return mots[0] if mots else None