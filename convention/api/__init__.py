import flask
import flask_httpauth


blueprint = flask.Blueprint("api", __name__)
token_auth = flask_httpauth.HTTPBasicAuth()


@blueprint.before_request
@token_auth.login_required
def _before_request():
    pass
