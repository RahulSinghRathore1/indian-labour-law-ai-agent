import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    CRAWL_SOURCES = [
        {
            'name': 'Ministry of Labour and Employment',
            'base_url': 'https://labour.gov.in',
            'endpoints': [
                '/whatsnew',
                '/acts',
                '/rules'
            ]
        },
        {
            'name': 'E-Gazette India',
            'base_url': 'https://egazette.gov.in',
            'endpoints': [
                '/SearchGazettes.aspx'
            ]
        }
    ]
    
    SIMILARITY_THRESHOLD = 0.85
    
    CONTENT_SIMILARITY_THRESHOLD = 0.95
    
    MAX_RETRIES = 3
    
    REQUEST_TIMEOUT = 30
    
    RATE_LIMIT_DELAY = 2
    
    BATCH_SIZE = 10
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/crawler.log'
    
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    
    LLM_MODEL = 'llama-3.1-8b-instant'
    
    API_HOST = '0.0.0.0'
    API_PORT = 5000

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()
