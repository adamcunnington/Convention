import flask

import convention
from convention import api, models


@api.blueprint.route("/")
def hello_world():
    return "Hello, World!"


@api.blueprint.route("/conventions/")
def get_conventions():
    return flask.jsonify([c.get_data() for c in models.Convention.query])


@api.blueprint.route("/conventions/<int:convention_key>")
def get_convention(convention_key):
    c = models.Convention.query.filter_by(key=convention_key).first()
    if c is None:
        flask.abort(404)
    return flask.jsonify(c.get_data())


@api.blueprint.route("/conventions/<int:convention_key>/validate/<s>")
def validate(convention_key, s):
    c = models.Convention.query.filter_by(key=convention_key).first()
    if c is None:
        flask.abort(404)
    return flask.jsonify(c.validate(s))


convention.app.register_blueprint(api.blueprint, url_prefix="/api")
