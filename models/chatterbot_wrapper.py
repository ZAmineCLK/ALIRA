# models/chatterbot_wrapper.py
from utils.logger import logger
from config.settings import PROJECT_NAME

def initialiser_chatterbot():
    try:
        from chatterbot import ChatBot
        from chatterbot.trainers import ListTrainer
        
        chatbot = ChatBot(PROJECT_NAME,
            logic_adapters=[{
                'import_path': 'chatterbot.logic.BestMatch',
                'default_response': 'Pouvez-vous reformuler, s\'il vous plaît ?',
                'maximum_similarity_threshold': 0.85
            }],
            database_uri=None
        )
        
        trainer = ListTrainer(chatbot)
        conversations_base = [
            ["Bonjour", "Salut ! Comment ça va ?"],
            ["Hello", "Bonjour !"],
            ["Salut", "Coucou ! Comment puis-je vous aider ?"],
            ["Comment ça va ?", "Je fonctionne parfaitement, merci ! Et vous ?"],
            ["Quelle heure est-il ?", "Je n'ai pas accès à l'heure en temps réel, désolée."],
            ["Quel est ton nom ?", f"Je m'appelle {PROJECT_NAME}, votre assistante d'apprentissage !"],
            ["Que fais-tu ?", "Je discute avec vous et j'apprends de nouvelles choses."],
            ["Merci", "De rien ! C'est un plaisir de vous aider."],
            ["Au revoir", "À bientôt ! Ce fut un plaisir de discuter."],
            ["Que peux-tu faire ?", "Je peux discuter, répondre à des questions, et apprendre de nouvelles choses !"],
            ["Comment apprends-tu ?", "Utilise 'apprends que [question] c\'est [réponse]' pour m'enseigner !"],
            ["aide", "Commandes spéciales:\n- apprends que [X] c'est [Y]\n- corrige [X] en [Y]\n- oublie [X]\n- statistiques"]
        ]
        
        for conv in conversations_base:
            trainer.train(conv)
        
        logger.info("ChatterBot initialisé et entraîné")
        return chatbot
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de ChatterBot: {e}")
        return None