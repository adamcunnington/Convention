import flask
import flask_httpauth

from convention import models


blueprint = flask.Blueprint("api", __name__)
token_auth = flask_httpauth.HTTPBasicAuth()


@blueprint.before_request
@token_auth.login_required
def _before_request():
    pass


@token_auth.verify_password
def _verify_token(token, password):
    flask.g.current_user = models.User.verify_auth_token(token)
    return flask.g.current_user is not None
