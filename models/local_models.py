# models/local_models.py
import torch
import re
from utils.logger import logger
from core.wikipedia_fallback import WikipediaFallback

class ModeleLocal:
    def __init__(self, nlp=None):
        self.modele_traduction_charge = False
        self.modele_generation_charge = False
        self.traducteur = None
        self.generateur = None
        self.nlp = nlp
        self.wikipedia_fallback = WikipediaFallback()
        
    def charger_modeles(self):
        try:
            logger.info("Chargement du modèle de traduction...")
            from transformers import MarianMTModel, MarianTokenizer
            self.modele_traduction_nom = "Helsinki-NLP/opus-mt-en-fr"
            self.tokenizer_traduction = MarianTokenizer.from_pretrained(self.modele_traduction_nom)
            self.modele_traduction = MarianMTModel.from_pretrained(self.modele_traduction_nom)
            self.modele_traduction_charge = True
            logger.info("Modèle de traduction chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur chargement modèle traduction: {e}")
        
        self.modele_generation_charge = False
        logger.info("Modèle de génération désactivé")
    
    def traduire_anglais_francais(self, texte_anglais):
        if not self.modele_traduction_charge or not texte_anglais:
            return texte_anglais
        
        try:
            inputs = self.tokenizer_traduction(texte_anglais, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                translated = self.modele_traduction.generate(**inputs)
            texte_francais = self.tokenizer_traduction.decode(translated[0], skip_special_tokens=True)
            return texte_francais
        except Exception as e:
            logger.error(f"Erreur traduction: {e}")
            return texte_anglais
    
    def detecter_langue(self, texte):
        if not texte:
            return "fr"
        
        mots_anglais = {"the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at"}
        mots_texte = set(texte.lower().split())
        
        if len(mots_texte) > 0 and len(mots_texte.intersection(mots_anglais)) / len(mots_texte) > 0.2:
            return "en"
        return "fr"
    
    def traiter_requete_multilingue(self, requete):
        if self.detecter_langue(requete) == "en":
            logger.info(f"🌐 Détection: Requête en anglais -> '{requete}'")
            requete_traduite = self.traduire_anglais_francais(requete)
            logger.info(f"🌐 Traduction: '{requete}' -> '{requete_traduite}'")
            return requete_traduite, True
        return requete, False
    
    def generer_reponse_avec_fallback(self, question, deja_verifie_memoire=False):
        if not deja_verifie_memoire:
            return None, None
        
        terme_recherche = self.wikipedia_fallback.extraire_terme_principal(question, self.nlp)
        if terme_recherche:
            logger.info(f"Recherche sur Wikipedia: '{terme_recherche}'")
            resultat_wikipedia = self.wikipedia_fallback.rechercher_wikipedia(terme_recherche)
            
            if resultat_wikipedia and self._reponse_pertinente(question, resultat_wikipedia):
                if len(resultat_wikipedia) > 250:
                    resultat_wikipedia = resultat_wikipedia[:247] + "..."
                reponse_finale = f"📚 D'après Wikipedia: {resultat_wikipedia}"
                logger.info(f"Réponse Wikipedia générée")
                return reponse_finale, "wikipedia"
        
        return None, None
    
    def _reponse_pertinente(self, question, reponse_wikipedia):
        question_lower = question.lower()
        reponse_lower = reponse_wikipedia.lower()
        
        if self.nlp:
            try:
                doc = self.nlp(question_lower)
                for token in doc:
                    if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and not token.is_stop and len(token.text) > 3):
                        if token.lemma_.lower() in reponse_lower:
                            return True
            except:
                pass
        
        mots_question = set(question_lower.split())
        mots_pertinents = {mot for mot in mots_question if len(mot) > 4 and mot not in ['bonjour', 'salut', 'hello', 'veux', 'savoir', 'trouver']}
        
        for mot in mots_pertinents:
            if mot in reponse_lower:
                return True
        
        return False