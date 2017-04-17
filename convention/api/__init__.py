import flask
import flask_httpauth


blueprint = flask.Blueprint("api", __name__)
token_auth = flask_httpauth.HTTPTokenAuth(scheme="token")


@blueprint.before_request
@token_auth.login_required
def before_request():
    pass
