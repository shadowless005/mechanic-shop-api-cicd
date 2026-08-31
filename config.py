class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:Johnny5587!@localhost/mechanic_shop"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///testing.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = "SimpleCache"