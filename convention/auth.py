import flask
import flask_login
from flask_oauthlib import client

import convention
from convention import models, utilities


blueprint = flask.Blueprint("auth", __name__)
login_manager = flask_login.LoginManager(convention.app)
login_manager.login_view = "users"
oauth = client.OAuth(convention.app)
convention.app.config["google"] = {
    "consumer_key": "776473556737-7eifgi9gjm63pmmcgn6qkpnce4kp36mp.apps.googleusercontent.com",
    "consumer_secret": "cZvTjiK3efZvvv-CB2mCSPe1"
}
oauth_providers = {
    "google": utilities.GoogleOAuth("google", oauth)
}


@blueprint.before_request
@flask_login.login_required
def before_request():
    pass


@login_manager.user_loader
def load_user(user_key):
    return models.User.query.get(int(user_key))
