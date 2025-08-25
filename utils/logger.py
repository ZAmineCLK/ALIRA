# utils/logger.py
import logging
import sys

def setup_logger():
    logger = logging.getLogger("CLARA")
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Handler fichier
    file_handler = logging.FileHandler("clara.log", encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()