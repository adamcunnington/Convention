import os


class Config(object):
    DEBUG = False
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.path.join(os.path.dirname(os.path.dirname(__file__)), "convention.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = r"sqlite:///:memory:"


CONFIGURATIONS = {
    "dev": DevelopmentConfig,
    "test": TestConfig
}
