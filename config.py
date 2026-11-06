import os
import secrets


def database_uri(value):
    """Use the installed psycopg2 driver for Render's Postgres URLs."""
    if value and value.startswith(('postgres://', 'postgresql://')):
        return 'postgresql+psycopg2://' + value.split('://', 1)[1]
    return value


class Config:
    SQLALCHEMY_DATABASE_URI = database_uri(os.getenv('DATABASE_URL')) or 'sqlite:///mechanic_shop_cicd_demo.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    CACHE_TYPE = 'SimpleCache'
    AUTO_CREATE_TABLES = True
    PRODUCTION = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'isolated-tests-only'
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = database_uri(os.getenv('DATABASE_URL'))
    SECRET_KEY = os.getenv('SECRET_KEY')
    AUTO_CREATE_TABLES = False
    PRODUCTION = True
