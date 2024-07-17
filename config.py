import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ASSEMBLY_API_KEY = os.getenv('ASSEMBLY_API_KEY')
    DEBUG = os.getenv('DEBUG')
    CRM_API_KEY = os.getenv('CRM_API_KEY')


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
