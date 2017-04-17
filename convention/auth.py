import flask
import flask_login

import convention
from convention import models


blueprint = flask.Blueprint("auth", __name__)
login_manager = flask_login.LoginManager(convention.app)
login_manager.login_view = "auth.index"


@blueprint.before_request
@login_manager.login_required
def before_request():
    pass


@flask_login.user_loader
def load_user(user_key):
    return models.User.get(int(user_key))
