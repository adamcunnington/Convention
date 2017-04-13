import flask

from convention import api, models


@api.blueprint.route("/")
def hello_world():
    return "Hello, World!"


@api.blueprint.route("/conventions/")
def get_conventions():
    return flask.jsonify(convention.get_data() for convention in models.Convention.query)
