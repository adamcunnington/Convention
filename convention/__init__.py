import os

import dotenv
import flask

from convention import config


_THIS_DIRECTORY = os.path.dirname(__file__)


app = flask.Flask(__name__, instance_path=os.path.join(_THIS_DIRECTORY, "instance"), instance_relative_config=True)
dotenv.load_dotenv(os.path.join(_THIS_DIRECTORY, "config.env"))
app.config.from_object(config.CONFIGURATIONS[os.environ.get("CONVENTION_CONFIG")])
app.config.from_pyfile(os.environ.get("CONVENTION_CONFIG_OVERRIDE_PATH"), silent=True)
