import flask

import convention


blueprint = flask.Blueprint("api", __name__)
convention.app.register_blueprint(blueprint, url_prefix="/api")
