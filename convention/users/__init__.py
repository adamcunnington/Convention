import flask
import flask_login

import convention
from convention import models


blueprint = flask.Blueprint("users", __name__)
login_manager = flask_login.LoginManager(convention.app)


@blueprint.before_request
@flask_login.login_required
def _before_request():
    pass


@login_manager.user_loader
def _load_user(user_key):
    return models.User.query.get(int(user_key))
