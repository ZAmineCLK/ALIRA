#!/usr/bin/env python3
"""
Initialisation d'ALIRA - Charge les connaissances de base
Version complète avec compréhension linguistique
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import logging
from dotenv import load_dotenv
import re
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alira_init.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ALIRA_INIT")

# Charger les variables d'environnement
load_dotenv()

class InitialisateurALIRA:
    """Classe pour initialiser la base de connaissances d'ALIRA"""
    
    def __init__(self):
        self.connection = self._get_connection()
    
    def _get_connection(self):
        """Établit une connexion MySQL"""
        try:
            config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'database': os.getenv('MYSQL_DATABASE', 'alira_db'),
                'user': os.getenv('MYSQL_USER', 'alira_user'),
                'password': os.getenv('MYSQL_PASSWORD', 'alira_password'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'charset': 'utf8mb4',
                'autocommit': True
            }
            connection = mysql.connector.connect(**config)
            if connection.is_connected():
                logger.info("✅ Connexion MySQL établie")
                return connection
            else:
                logger.error("❌ Connexion MySQL échouée")
                return None
        except Error as e:
            logger.error(f"❌ Erreur de connexion MySQL: {e}")
            return None
    
    def normaliser_question(self, question):
        """Normalise les questions pour la base de données"""
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
        
        question_normalisee = re.sub(r'[?¿!¡]', '', question_normalisee).strip()
        question_normalisee = re.sub(r'\s+', ' ', question_normalisee)
        return question_normalisee
    
    def charger_connaissances_de_base(self):
        """Charge les connaissances de base dans la base de données"""
        if not self.connection:
            logger.error("❌ Impossible de charger les connaissances: connexion absente")
            return False
        
        # Connaissances de base organisées par catégories
        connaissances = [
            # 🌟 SALUTATIONS ET PRÉSENTATION
            ("bonjour", "Salutations ! Je suis ALIRA, votre assistant conversationnel. Comment puis-je vous aider aujourd'hui ?"),
            ("salut", "Salut ! Je suis ALIRA, prêt à répondre à vos questions."),
            ("hello", "Hello ! Je suis ALIRA, votre assistant intelligent."),
            ("coucou", "Coucou ! Ravie de vous parler. Je suis ALIRA."),
            ("qui es-tu", "Je suis ALIRA (Accompagnante Libre à Interaction et Réflexion Assistée), un assistant conversationnel conçu pour vous aider et apprendre de vous."),
            ("présente toi", "Je m'appelle ALIRA, qui signifie Accompagnante Libre à Interaction et Réflexion Assistée. Je suis un assistant conversationnel qui apprend au fur et à mesure de nos discussions."),
            
            # 🏛️ MYTHOLOGIE ET HISTOIRE (thème central)
            ("nymphes", "Les nymphes sont des divinités mineures de la nature dans la mythologie grecque. Elles sont associées aux forêts, montagnes, rivières et sources, et représentent les esprits de la nature."),
            ("oracle", "Un oracle dans la mythologie grecque est un lieu ou une personne qui transmet des prophéties et des conseils divins. Le plus célèbre est l'oracle de Delphes, dédié à Apollon."),
            ("athéna", "Athéna est la déesse de la sagesse, de la stratégie militaire, des arts et de l'artisanat dans la mythologie grecque. Elle est née directement de la tête de Zeus, toute armée."),
            ("zeus", "Zeus est le roi des dieux dans la mythologie grecque. Il est le dieu du ciel, du tonnerre et de la foudre. Il règne sur l'Olympe et est le père de nombreux dieux et héros."),
            ("mythologie", "La mythologie est l'ensemble des mythes et légendes d'une culture ou d'une religion. La mythologie grecque est particulièrement riche et influence encore notre culture aujourd'hui."),
            ("divin", "Le divin fait référence à ce qui appartient aux dieux ou à Dieu, qui possède une nature sacrée ou surnaturelle. Dans les mythologies, les divinités ont souvent des pouvoirs extraordinaires."),
            
            # 📚 CONNAISSANCES GÉNÉRALES
            ("intelligence artificielle", "L'intelligence artificielle (IA) est un domaine de l'informatique qui crée des systèmes capables de réaliser des tâches nécessitant normalement l'intelligence humaine, comme la reconnaissance vocale, la prise de décision ou la traduction."),
            ("ordinateur", "Un ordinateur est une machine électronique qui traite des données selon des instructions programmées. Il peut effectuer des calculs, stocker des informations et exécuter diverses tâches complexes."),
            ("internet", "Internet est un réseau mondial qui connecte des millions d'ordinateurs et d'appareils. Il permet l'échange d'informations, la communication et l'accès à d'innombrables ressources en ligne."),
            ("programmation", "La programmation est le processus qui consiste à écrire du code informatique pour créer des logiciels, des applications et des sites web. Les programmeurs utilisent des langages comme Python, Java ou JavaScript."),
            
            # 🌍 GÉOGRAPHIE
            ("paris", "Paris est la capitale de la France, située dans le nord du pays sur les rives de la Seine. Elle est réputée pour sa culture, son art, sa gastronomie et ses monuments comme la Tour Eiffel et Notre-Dame."),
            ("france", "La France est un pays d'Europe occidentale. Elle est connue pour sa riche histoire, sa culture, sa gastronomie et ses paysages variés, allant des plages de la Méditerranée aux montagnes des Alpes."),
            ("europe", "L'Europe est un continent situé dans l'hémisphère nord. Elle compte une cinquantaine de pays et est connue pour son histoire riche, sa diversité culturelle et son influence sur le monde entier."),
            
            # 👨‍👩‍👧‍👦 SOCIÉTÉ ET RELATIONS
            ("famille", "Une famille est un groupe de personnes liées par le sang, le mariage ou l'adoption. Elle constitue l'unité de base de nombreuses sociétés et offre soutien, affection et éducation."),
            ("amitié", "L'amitié est une relation affective entre deux ou plusieurs personnes, basée sur la confiance, le respect mutuel et des intérêts communs. C'est un lien précieux qui enrichit la vie."),
            ("amour", "L'amour est un sentiment profond d'affection et d'attachement envers quelqu'un ou quelque chose. Il peut prendre de nombreuses formes : amour familial, amical, romantique ou passionnel."),
            ("éducation", "L'éducation est le processus d'apprentissage et d'acquisition de connaissances, compétences, valeurs et attitudes. Elle se fait à l'école, en famille et tout au long de la vie."),
            
            # 🔧 TECHNOLOGIE
            ("robot", "Un robot est une machine programmable capable d'effectuer automatiquement des tâches complexes. Les robots sont utilisés dans l'industrie, la médecine, l'exploration spatiale et de nombreux autres domaines."),
            ("application", "Une application (ou app) est un programme informatique conçu pour réaliser une tâche spécifique sur un ordinateur, un smartphone ou une tablette. Exemples : navigateur web, jeu, outil de productivité."),
            ("smartphone", "Un smartphone est un téléphone mobile intelligent qui combine les fonctions d'un téléphone avec celles d'un ordinateur portable. Il permet d'installer des applications, naviguer sur internet, etc."),
            
            # ❓ QUESTIONS FRÉQUENTES
            ("comment ça va", "Je fonctionne parfaitement, merci de demander ! Je suis un programme informatique, donc je n'ai pas de sentiments, mais je suis prêt à vous aider."),
            ("quelle heure est-il", "En tant qu'assistant, je n'ai pas accès direct à l'heure en temps réel. Vous pouvez consulter l'heure sur votre appareil ou me demander d'autres informations !"),
            ("quel temps fait-il", "Je n'ai pas actuellement la capacité de fournir des informations météorologiques en temps réel. Je me spécialise dans les connaissances générales et l'apprentissage conversationnel."),
            
            # 🎨 ARTS ET CULTURE
            ("musique", "La musique est l'art d'arranger les sons et les silences dans le temps. Elle utilise des éléments comme la mélodie, l'harmonie, le rythme et le timbre pour créer une expression artistique."),
            ("art", "L'art est une diverse gamme d'activités humaines créatives exprimant une vision technique, belle, émotionnelle ou conceptuelle. Il inclut la peinture, la sculpture, la musique, la littérature, etc."),
            ("livre", "Un livre est un ensemble de pages écrites ou imprimées reliées ensemble. Les livres permettent de préserver et transmettre des connaissances, des histoires et des idées à travers le temps et l'espace."),
            
            # 🏥 SANTÉ ET BIEN-ÊTRE
            ("santé", "La santé est un état de complet bien-être physique, mental et social, et ne consiste pas seulement en une absence de maladie ou d'infirmité. Elle est essentielle à une vie épanouie."),
            ("sport", "Le sport est une activité physique régie par des règles, souvent compétitive, qui vise à améliorer la condition physique, développer des compétences et offrir du divertissement."),
            ("nutrition", "La nutrition est la science qui étudie les aliments et leur utilisation par l'organisme. Une alimentation équilibrée est cruciale pour maintenir une bonne santé et prévenir les maladies."),
            
            # 💼 TRAVAIL AND ÉCONOMIE
            ("travail", "Le travail est une activité humaine organisée et utile, généralement rémunérée, qui contribue à la production de biens et services. Il permet de subvenir à ses besoins et de participer à la société."),
            ("argent", "L'argent est un moyen d'échange utilisé pour acquérir des biens et services. Il facilite les transactions économiques et sert également d'unité de compte et de réserve de valeur."),
            ("économie", "L'économie est la science sociale qui étudie la production, la distribution et la consommation de biens et services. Elle analyse comment les sociétés utilisent des ressources limitées."),
            
            # 🌱 NATURE ET ENVIRONNEMENT
            ("nature", "La nature désigne l'ensemble des phénomènes et êtres qui constituent l'univers, indépendamment de l'action humaine. Elle inclut les paysages, les animaux, les plantes et les écosystèmes."),
            ("environnement", "L'environnement est l'ensemble des éléments naturels et artificiels dans lesquels les êtres vivants évoluent. Sa protection est cruciale pour la survie de la planète et des espèces."),
            ("climat", "Le climat est la distribution statistique des conditions atmosphériques dans une région donnée pendant une longue période. Le changement climatique actuel est un enjeu environnemental majeur."),
            
            # 🚗 TRANSPORT ET VOYAGE
            ("voiture", "Une voiture est un véhicule motorisé à roues utilisé principalement pour le transport de personnes. Elle comporte généralement un moteur, quatre roues et peut transporter de 2 à 9 personnes."),
            ("voyage", "Un voyage est le déplacement d'une personne ou d'un groupe entre des lieux géographiques éloignés. Les voyages permettent de découvrir de nouvelles cultures, paysages et expériences."),
            ("avion", "Un avion est un aéronef plus lourd que l'air, propulsé par un moteir, qui utilise des surfaces fixes (ailes) pour générer de la portance et voler dans l'atmosphère."),
            
            # 🎓 ÉDUCATION ET APPRENTISSAGE
            ("école", "Une école est un établissement où l'on dispense un enseignement collectif. Elle joue un rôle crucial dans l'éducation des enfants et la transmission des connaissances et valeurs sociales."),
            ("université", "Une université est une institution d'enseignement supérieur qui délivre des diplômes dans diverses disciplines. Elle combine enseignement et recherche avancée."),
            ("apprentissage", "L'apprentissage est le processus d'acquisition de nouvelles connaissances, compétences, comportements ou préférences. Il peut être formel (école) ou informel (expérience)."),
            
            # 🍔 ALIMENTATION
            ("nourriture", "La nourriture est toute substance consommée pour fournir un soutien nutritionnel à un organisme. Elle est généralement d'origine végétale, animale ou fongique et contient des nutriments essentiels."),
            ("cuisine", "La cuisine est à la fois l'art de préparer les aliments et l'espace où cette préparation a lieu. Chaque culture a ses traditions culinaires et ses spécialités gastronomiques."),
            ("restaurant", "Un restaurant est un établissement commercial où l'on sert des plats préparés et des boissons à consommer sur place, en échange d'un paiement. Il existe différents types de restaurants selon les cuisines et services."),
            
            # 🏠 VIE QUOTIDIENNE
            ("maison", "Une maison est un bâtiment destiné à l'habitation, offrant un abri et un espace de vie pour une ou plusieurs personnes. C'est un lieu de repos, de vie familiale et d'intimité."),
            ("ville", "Une ville est une agglomération humaine importante caractérisée par une forte densité de population, des infrastructures développées et diverses activités économiques, culturelles et sociales."),
            ("campagne", "La campagne désigne les espaces ruraux, par opposition aux zones urbaines. Elle est caractérisée par une faible densité de population et une dominance des activités agricoles et naturelles."),
            
            # ⚽ LOISIRS ET DIVERTISSEMENT
            ("jeu", "Un jeu est une activité de loisir organisée par des règles, entreprise pour le plaisir. Les jeux peuvent être physiques (sports), mentaux (échecs) ou électroniques (jeux vidéo)."),
            ("film", "Un film est une œuvre cinématographique qui raconte une histoire à travers une succession d'images animées. Le cinéma est à la fois un art, une industrie et un divertissement populaire."),
            ("lecture", "La lecture est l'activité qui consiste à prendre connaissance d'un texte écrit. Elle permet d'acquérir des connaissances, de se divertir et de développer son imagination et sa réflexion."),
            
            # 🔬 SCIENCE ET TECHNOLOGIE
            ("science", "La science est une entreprise systématique qui construit et organise la connaissance sous forme d'explications et de prédictions testables sur l'univers. Elle repose sur l'observation, l'expérimentation et la méthode scientifique."),
            ("technologie", "La technologie est l'application des connaissances scientifiques à des fins pratiques, particulièrement dans l'industrie. Elle englobe les techniques, méthodes, machines et outils utilisés pour résoudre des problèmes."),
            ("recherche", "La recherche est un processus systématique d'investigation et d'étude visant à découvrir de nouvelles connaissances ou à développer de nouvelles applications. Elle est fondamentale pour le progrès scientifique et technologique."),
            
            # 💡 CONCEPTS ABSTRAITS
            ("liberté", "La liberté est la capacité d'agir selon sa volonté sans être entravé par le pouvoir d'autrui. C'est un concept fondamental en philosophie, en politique et en droit, souvent associé à la responsabilité."),
            ("justice", "La justice est un principe moral qui exige le respect du droit, de l'équité et de l'impartialité. Elle vise à garantir que chacun reçoive ce qui lui est dû et que les torts soient réparés."),
            ("bonheur", "Le bonheur est un état de satisfaction complète caractérisé par sa stabilité et sa durée. Il ne s'agit pas d'une joie intense mais d'une plénitude agréable, une harmonie avec soi-même et son environnement."),
            
            # 🎭 ÉMOTIONS ET PSYCHOLOGIE
            ("émotion", "Une émotion est une réaction psychologique et physiologique à une situation. Les émotions de base incluent la joie, la tristesse, la colère, la peur, la surprise et le dégoût. Elles influencent nos pensées et comportements."),
            ("psychologie", "La psychologie est la science qui étudie les comportements, les processus mentaux et les émotions des êtres humains. Elle cherche à comprendre comment nous pensons, ressentons et agissons dans différentes situations."),
            ("stress", "Le stress est une réponse physiologique et psychologique à une situation perçue comme exigeante ou menaçante. Un stress modéré peut être motivant, mais un stress excessif peut nuire à la santé."),
            
            # 📱 COMMUNICATION ET MÉDIAS
            ("communication", "La communication est l'action de transmettre des informations, des idées ou des sentiments entre des individus ou des groupes. Elle peut être verbale, non verbale, écrite ou visuelle."),
            ("réseaux sociaux", "Les réseaux sociaux sont des plateformes en ligne qui permettent aux utilisateurs de créer du contenu, de partager des informations et d'interagir avec d'autres personnes. Exemples : Facebook, Twitter, Instagram."),
            
            # 🛒 COMMERCE ET CONSOMMATION
            ("commerce", "Le commerce est l'activité d'achat et de vente de biens et services. Il peut être local, national ou international (import/export) et se fait dans des magasins physiques ou en ligne."),
            ("consommation", "La consommation est l'action d'utiliser des biens et services pour satisfaire des besoins ou désirs. Dans les économies modernes, elle est un moteur important de l'activité économique."),
            
            # 🌐 MONDE GLOBAL
            ("globalisation", "La globalisation (ou mondialisation) est le processus d'intégration internationale résultant de l'échange de produits, d'informations, de travail et de culture. Elle crée une interdépendance croissante entre les pays."),
            ("culture", "La culture englobe les connaissances, croyances, arts, lois, coutumes et habitudes acquises par l'homme en tant que membre de la société. Elle est transmise de génération en génération et varie selon les groupes humains."),
            ("diversité", "La diversité fait référence à la variété et aux différences entre les individus et les groupes humains. Elle peut concerner la culture, l'ethnicité, le genre, l'âge, les capacités, les croyances et bien d'autres aspects."),
            
            # ⏰ TEMPS ET HISTOIRE
            ("histoire", "L'histoire est à la fois l'étude et le récit des événements passés concernant l'humanité. Elle cherche à comprendre le présent à la lumière du passé et à préserve la mémoire collective."),
            ("temps", "Le temps est une notion fondamentale qui marque la succession des événements. En physique, c'est une dimension dans laquelle les événements se succèdent du passé vers le futur. Philosophiquement, c'est une condition de l'existence."),
            ("futur", "Le futur est l'ensemble des événements qui n'ont pas encore eu lieu. Il est incertain et fait l'objet de projections, de plans et de prévisions dans tous les domaines de l'activité humaine."),
            
            # 🎯 BUTS ET MOTIVATION
            ("objectif", "Un objectif est un résultat spécifique qu'une personne ou organisation cherche à atteindre. Fixer des objectifs clairs est important pour orienter les efforts et mesurer le progrès."),
            ("motivation", "La motivation est ce qui pousse un individu à agir pour atteindre un objectif. Elle peut être intrinsèque (plaisir de l'action) ou extrinsèque (récompense externe)."),
            ("réussite", "La réussite est l'atteinte d'un objectif ou la réalisation satisfaisante d'une entreprise. Elle est souvent associée à l'accomplissement personnel, professionnel ou social."),
            
            # 🤝 RELATIONS SOCIALES
            ("société", "Une société est un groupe d'individus unis par des relations sociales, partageant généralement un territoire, une culture et des institutions. Les sociétés humaines sont complexe et organisées."),
            ("communauté", "Une communauté est un groupe social dont les membres partagent quelque chose en commun : lieu de résidence, intérêts, valeurs, identité. Elle crée un sentiment d'appartenance et de solidarité."),
            ("coopération", "La coopération est l'action de travailler ensemble vers un objectif commun. Elle implique la coordination des efforts, le partage des ressources et l'entraide pour atteindre des résultats que seul serait difficile d'obtenir."),
            
            # 🎨 CRÉATIVITÉ ET INNOVATION
            ("créativité", "La créativité est la capacité à produire des idées, solutions ou œuvres originales et adaptées à un contexte. Elle combine imagination, pensée divergente et expertise dans un domaine."),
            ("innovation", "L'innovation est la mise en œuvre réussie d'idées nouvelles créant de la valeur. Elle peut concerner des produits, services, processus ou modèles d'affaires et est cruciale pour le progrès."),
            ("imagination", "L'imagination est la capacité à forme des images, idées ou concepts mentaux qui ne sont pas présents aux sens. Elle est fondamentale pour la créativité, la résolution de problèmes et l'anticipation."),
            
            # 🛡️ SÉCURITÉ ET PROTECTION
            ("sécurité", "La sécurité est l'état d'être protégé contre le danger, le risque ou la menace. Elle peut concerner la sécurité physique, économique, numérique ou environnementale et est un besoin fondamental."),
            ("protection", "La protection est l'action de défendre, préserver ou mettre à l'abri du danger, de la destruction ou des influences néfastes. Elle peut s'appliquer aux personnes, aux biens, à l'environnement ou aux données."),
            
            # 📈 CROISSANCE ET DÉVELOPPEMENT
            ("développement", "Le développement est le processus d'amélioration progressive qui conduit à la croissance, à la maturation ou à l'évolution. Il peut concerner les individus (développement personnel), les organisations ou les sociétés."),
            ("croissance", "La croissance est l'augmentation de la taille, de la quantité ou de la valeur. En économie, elle se mesure souvent par l'augmentation du PIB. Pour les individus, elle peut être physique, intellectuelle ou spirituelle."),
            ("progrès", "Le progrès est l'avancement vers une condition meilleure, plus avancée ou plus perfectionnée. Il implique des améliorations dans les domaines technologique, social, économique ou moral."),
            
            # 🌟 QUALITÉS PERSONNELLES
            ("patience", "La patience est la capacité à endurer des difficultés, des retards ou des inconforts sans se mettre en colère ou s'énerver. C'est une vertu qui permet de persévérer face aux obstacles."),
            ("persévérance", "La persévérance est la qualité qui permet de continuer à essayer malgré les difficultés, les échecs ou l'opposition. Elle est essentielle pour atteindre des objectifs à long terme."),
            ("curiosité", "La curiosité est le désir d'apprendre, de découvrir et de comprendre de nouvelles choses. Elle pousse à explorer, poser des questions et chercher des connaissances au-delà de ce qui est immédiatement nécessaire."),
            
            # 🎉 CÉLÉBRATIONS ET TRADITIONS
            ("fête", "Une fête est un événement social ou culturel marquant une occasion spéciale, souvent célébré par des rassemblements, des repas, de la musique et des activités joyeuses."),
            ("tradition", "Une tradition est une pratique, croyance ou coutume transmise de génération en génération. Elle relie les communautés à leur passé et contribue à maintenir leur identité culturelle."),
            ("célébration", "Une célébration est l'action de marquer un événement important par des activités spéciales. Elle permet de renforcer les liens sociaux, d'honorer des réalisations et de créer des souvenirs partagés."),
            
            # 🚀 TECHNOLOGIES EMERGENTES
            ("réalité virtuelle", "La réalité virtuelle (RV) est une technologie qui crée un environnement simulé immersif, généralement à l'aide d'un casque. Les utilisateurs peuvent interagir avec cet environnement comme s'ils y étaient physiquement."),
            ("blockchain", "La blockchain est une technologie de stockage et de transmission d'informations, transparente, sécurisée, et fonctionnant sans organe central de contrôle. Elle est la base des cryptomonnaies comme le Bitcoin."),
            
            # 🏥 SANTÉ MENTALE
            ("bien-être", "Le bien-être est un état d'équilibre et d'épanouissement comprenant la santé physique, mentale et sociale. Il va au-delà de l'absence de maladie et inclut la satisfaction et la qualité de vie."),
            ("méditation", "La méditation est une pratique qui entraîne l'esprit à se concentrer et à rediriger les pensées. Elle est souvent utilisée pour réduire le stress, augmenter la conscience de soi et promouvoir la relaxation."),
            ("pleine conscience", "La pleine conscience (mindfulness) est la pratique qui consiste à porter attention au moment présent, délibérément et sans jugement. Elle aide à réduire le stress et à améliorer le bien-être mental."),
            
            # 🌍 ENJEUX MONDAUX
            ("changement climatique", "Le changement climatique désigne les modifications durables du climat de la Terre, principalement causées par les activités humaines comme l'émission de gaz à effet de serre. C'est un enjeu environnemental majeur du 21e siècle."),
            ("développement durable", "Le développement durable est un mode de développement qui répond aux besoins du présent sans compromettre la capacité des générations futures à répondre aux leurs. Il intègre les aspects environnementaux, sociaux et économiques."),
            ("biodiversité", "La biodiversité est la variété des formes de vie sur Terre, incluant la diversité des espèces, des gènes et des écosystèmes. Sa préservation est cruciale pour la santé de la planète et le bien-être humain."),
            
            # 💼 LEADERSHIP ET MANAGEMENT
            ("leadership", "Le leadership est la capacité d'influencer, motiver et permettre à d'autres de contribuer à l'efficacité et au succès d'une organisation. Un bon leader inspire confiance et guide vers des objectifs communs."),
            ("management", "Le management est l'art de diriger une organisation et de prendre des décisions pour atteindre des objectifs. Il implique la planification, l'organisation, la direction et le contrôle des ressources."),
            ("équipe", "Une équipe est un groupe de personnes travaillant ensemble vers un objective commun. Le travail d'équipe efficace combine les compétences complémentaires des membres et favorise la collaboration."),
            
            # 📊 DONNÉES ET INFORMATION
            ("donnée", "Une donnée est une valeur ou un fait brut, souvent numérique, qui représente une information. Les données deviennent de l'information lorsqu'elles sont organisées et interprétées dans un contexte."),
            ("information", "L'information est une donnée traitée et organisée qui a un sens dans un contexte particulier. À l'ère numérique, la gestion de l'information est cruciale pour la prise de décision."),
            ("connaissance", "La connaissance est la compréhension, la conscience ou la familiarité acquise through l'expérience ou l'éducation. Elle représente l'information assimilée et comprise, permettant une action éclairée."),
            
            # 🎓 COMPÉTENCES DU 21E SIÈCLE
            ("pensée critique", "La pensée critique est la capacité à analyser objectivement des informations et des idées pour former un jugement raisonné. Elle implique le questionnement, l'évaluation des preuves et la remise en cause des assumptions."),
            ("résolution de problèmes", "La résolution de problèmes est le processus d'identification d'un problème, de génération de solutions alternatives, et de mise en œuvre et d'évaluation de la solution choisie. C'est une compétence essentielle dans tous les domaines."),
            ("adaptabilité", "L'adaptabilité est la capacité à s'ajuster efficacement à des situations, environnements ou conditions changeants. Dans un monde en évolution rapide, c'est une compétence cruciale pour le succès personnel et professionnel."),
            
            # 🤖 ROBOTIQUE ET AUTOMATION
            ("robotique", "La robotique est un domaine interdisciplinaire qui combine l'ingénierie, l'informatique et d'autres fields pour concevoir, construire et utiliser des robots. Les robots peuvent effectuer des tâches dangereuses, répétitives ou précises."),
            ("automatisation", "L'automatisation est l'utilisation de systèmes technologiques pour effectuer des processus avec un minimum d'intervention humaine. Elle augmente l'efficacité, la précision et la productivité dans de nombreux secteurs."),
            
            # 🎭 ÉMOTIONS AVANCÉES
            ("empathie", "L'empathie est la capacité à comprendre et à partager les sentiments d'une autre personne. Elle permet de se mettre à la place des autres et de répondre de manière appropriée à leurs émotions."),
            ("résilience", "La résilience est la capacité à surmonter les adversités, les traumatismes ou les stress importants et à continuer à fonctionner de manière saine. C'est la force de rebondir après les difficultés."),
            ("confiance", "La confiance est la conviction que quelqu'un ou quelque chose est fiable, bon, honnête ou efficace. Elle est fondamentale pour les relations humaines et le fonctionnement des sociétés."),
        ]
        
        try:
            cursor = self.connection.cursor()
            compteur = 0
            
            for question, reponse in connaissances:
                question_normalisee = self.normaliser_question(question)
                
                # Vérifier si la connaissance existe déjà
                cursor.execute("SELECT id FROM chatbot_memory WHERE question_normalized = %s", (question_normalisee,))
                existe = cursor.fetchone()
                
                if not existe:
                    cursor.execute("""
                    INSERT INTO chatbot_memory (question_normalized, response, learn_count)
                    VALUES (%s, %s, 1)
                    """, (question_normalisee, reponse))
                    
                    compteur += 1
                    logger.info(f"➕ Ajout: {question_normalisee}")
                else:
                    logger.info(f"⏩ Déjà existant: {question_normalisee}")
            
            # Mise à jour des statistiques
            cursor.execute("""
            INSERT INTO learning_stats (stat_key, stat_value)
            VALUES ('connaissances_base', %s)
            ON DUPLICATE KEY UPDATE stat_value = VALUES(stat_value)
            """, (compteur,))
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ {compteur} connaissances de base chargées avec succès")
            return True
            
        except Error as e:
            logger.error(f"❌ Erreur lors du chargement des connaissances: {e}")
            return False
    
    def creer_structure_semantique(self):
        """Crée la structure sémantique de base"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Concepts sémantiques de base
            concepts_semantiques = [
                ("technology", json.dumps(["informatique", "digital", "électronique", "innovation"]), json.dumps(["science", "innovation"])),
                ("science", json.dumps(["connaissance", "recherche", "découverte", "méthode"]), json.dumps(["éducation", "savoir"])),
                ("education", json.dumps(["apprentissage", "enseignement", "savoir", "connaissance"]), json.dumps(["développement", "culture"])),
                ("culture", json.dumps(["art", "tradition", "société", "histoire"]), json.dumps(["éducation", "société"])),
                ("santé", json.dumps(["bien-être", "médecine", "hygiène", "forme"]), json.dumps(["vie", "corps"])),
                ("nature", json.dumps(["environnement", "écologie", "faune", "flore"]), json.dumps(["science", "vie"])),
            ]
            
            for concept, synonyms, categories in concepts_semantiques:
                cursor.execute("""
                INSERT INTO concepts_semantiques (concept_principal, synonyms, categories)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE synonyms = VALUES(synonyms), categories = VALUES(categories)
                """, (concept, synonyms, categories))
            
            self.connection.commit()
            cursor.close()
            logger.info("✅ Structure sémantique créée avec succès")
            return True
            
        except Error as e:
            logger.error(f"❌ Erreur création structure sémantique: {e}")
            return False

def main():
    """Fonction principale d'initialisation"""
    print("🔧 Initialisation des connaissances de base d'ALIRA...")
    print("=" * 60)
    
    initialisateur = InitialisateurALIRA()
    if not initialisateur.connection:
        print("❌ Impossible de se connecter à la base de données")
        print("💡 Vérifiez votre configuration MySQL dans le fichier .env")
        return
    
    print("📦 Chargement des connaissances de base...")
    if initialisateur.charger_connaissances_de_base():
        print("✅ Connaissances de base chargées avec succès !")
        
        print("🧠 Création de la structure sémantique...")
        if initialisateur.creer_structure_semantique():
            print("✅ Structure sémantique créée avec succès !")
        else:
            print("⚠️ Structure sémantique partiellement créée")
    else:
        print("❌ Erreur lors du chargement des connaissances")
    
    print("=" * 60)
    print("🎯 ALIRA est maintenant prêt à fonctionner !")
    print("💡 Lancez le programme principal avec: python alira_core.py")
    print("=" * 60)

if __name__ == "__main__":
    main()