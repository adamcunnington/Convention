import os


class Config(object):
    DEBUG = False
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OAUTH_CREDENTIALS = {
        "facebook": {
            "consumer_key": os.environ.get("CONVENTION_FACEBOOK_CONSUMER_KEY"),
            "consumer_secret": os.environ.get("CONVENTION_FACEBOOK_CONSUMER_SECRET")
        },
        "google": {
            "consumer_key": os.environ.get("CONVENTION_GOOGLE_CONSUMER_KEY"),
            "consumer_secret": os.environ.get("CONVENTION_GOOGLE_CONSUMER_SECRET")
        }
    }


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
