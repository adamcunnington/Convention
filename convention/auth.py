import flask
import flask_login
from flask_oauthlib import client

import convention
from convention import models, utilities


blueprint = flask.Blueprint("auth", __name__)
login_manager = flask_login.LoginManager(convention.app)
oauth = client.OAuth(convention.app)

_GOOGLE = "google"
oauth_providers = {
    _GOOGLE: utilities.GoogleOAuth(_GOOGLE, oauth, convention.app.config["OAUTH_CREDENTIALS"][_GOOGLE])
}


@blueprint.before_request
@flask_login.login_required
def _before_request():
    pass


@login_manager.user_loader
def _load_user(user_key):
    return models.User.query.get(int(user_key))
