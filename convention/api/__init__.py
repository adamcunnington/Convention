import flask
import flask_httpauth

from convention import models


blueprint = flask.Blueprint("api", __name__)
password_auth = flask_httpauth.HTTPBasicAuth()
token_auth = flask_httpauth.HTTPBasicAuth()


@password_auth.verify_password
def _verify_credentials(email, password):
    flask.g.current_user = models.User.query.filter_by(email=email).first()
    if flask.g.current_user is None:
        return False
    return flask.g.current_user.verify_password(password)


@blueprint.before_request
@token_auth.login_required
def _before_request():
    pass


@token_auth.verify_password
def _verify_token(token, password):
    flask.g.current_user = models.User.verify_auth_token(token)
    return flask.g.current_user is not None
