# core/assistant_model.py
import re
from utils.logger import logger

class AssistantPhaseBebe:
    def __init__(self, nlp=None):
        self.nlp = nlp
        self.modele_charge = False
        self.modele = None
        self.tokenizer = None
        
    def charger_modele_assistant(self):
        try:
            logger.info("Chargement du modèle assistant pour phase bébé...")
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            modele_nom = "microsoft/DialoGPT-medium"
            self.tokenizer = AutoTokenizer.from_pretrained(modele_nom)
            self.modele = AutoModelForCausalLM.from_pretrained(modele_nom)
            
            self.generateur = pipeline(
                "text-generation",
                model=self.modele,
                tokenizer=self.tokenizer,
                max_length=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            self.modele_charge = True
            logger.info("Modèle assistant chargé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur chargement modèle assistant: {e}")
            try:
                from transformers import pipeline
                logger.info("Tentative avec modèle de fallback...")
                self.generateur = pipeline("text-generation", model="gpt2", max_length=150, temperature=0.7)
                self.modele_charge = True
                logger.info("Modèle de fallback chargé")
                return True
            except Exception as e2:
                logger.error(f"Erreur chargement fallback: {e2}")
                return False
    
    def generer_reponse_assistante(self, question, conversation_historique=None):
        if not self.modele_charge or not question:
            return None
        
        try:
            prompt = self._preparer_prompt(question, conversation_historique)
            reponses = self.generateur(prompt, max_new_tokens=150, num_return_sequences=1, temperature=0.8, top_p=0.9, repetition_penalty=1.1)
            
            if reponses and len(reponses) > 0:
                reponse_brute = reponses[0]['generated_text']
                reponse = self._nettoyer_reponse(reponse_brute, prompt)
                if reponse:
                    return f"👶 {reponse}"
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur génération assistante: {e}")
            return None
    
    def _preparer_prompt(self, question, historique):
        prompt = "Vous êtes CLARA, une assistante conversationnelle intelligente. Répondez de manière helpful et concise.\n\n"
        if historique and len(historique) > 0:
            for i, (user, bot) in enumerate(historique[-3:]):
                prompt += f"Utilisateur: {user}\nCLARA: {bot}\n\n"
        prompt += f"Utilisateur: {question}\nCLARA:"
        return prompt
    
    def _nettoyer_reponse(self, reponse_brute, prompt):
        if prompt in reponse_brute:
            reponse = reponse_brute.replace(prompt, "").strip()
        else:
            reponse = reponse_brute.strip()
        
        reponse = re.sub(r'\b(\w+)(?:\s+\1\b)+', r'\1', reponse)
        reponse = re.sub(r'[.,!?;]+$', '', reponse)
        
        if len(reponse) > 150:
            reponse = reponse[:147] + "..."
        
        return reponse if reponse and len(reponse) > 5 else None