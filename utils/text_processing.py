# utils/text_processing.py
import re
from .logger import logger

def corriger_fautes_typo(phrase):
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