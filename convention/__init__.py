import os

import dotenv
import flask

from convention import config


app = flask.Flask(__name__, instance_relative_config=True)
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__))), "config.env")
app.config.from_object(config.CONFIGURATIONS[os.environ.get("CONVENTION_CONFIG")])
app.config.from_pyfile(os.environ.get("CONVENTION_CONFIG_OVERRIDE_PATH"), silent=True)
