import flask
from flask_oauthlib import client

import convention
from convention import utilities


blueprint = flask.Blueprint("auth", __name__, template_folder="../auth/templates")
oauth = client.OAuth(convention.app)

_CREDENTIALS = convention.app.config["OAUTH_CREDENTIALS"]
_GOOGLE = "google"
_GOOGLE_CREDENTIALS = _CREDENTIALS[_GOOGLE]
oauth_providers = {
    _GOOGLE: utilities.GoogleOAuth(_GOOGLE, oauth, _GOOGLE_CREDENTIALS["key"], _GOOGLE_CREDENTIALS["secret"])
}
