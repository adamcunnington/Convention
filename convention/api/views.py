import flask
import flask_login

import convention
from convention import api, models


def _get_convention(convention_key):
    c = models.Convention.query.filter_by(user=flask_login.current_user, key=convention_key).first()
    if c is None:
        flask.abort(404)
    return c


@api.blueprint.route("/conventions/", methods=["POST"])
def add_convention():
    data = flask.request.get_json(force=True)
    c = models.Convention(data["name"], flask_login.current_user, data["pattern"], data.get("is_regex", False), data.get("allowable_values"),
                          data.get("allowable_combinations"))
    models.db.session.add(c)
    models.db.session.commit()
    return flask.jsonify({}, 201, {"Location": c.get_url()})


@api.blueprint.route("/conventions/<int:convention_key>", methods=["DELETE"])
def delete_convention(convention_key):
    models.db.session.delete(_get_convention(convention_key))
    models.db.session.commit()
    return flask.jsonify({})


@api.blueprint.route("/conventions/")
def get_conventions():
    x = [c.get_data() for c in models.Convention.query.filter_by(user=flask_login.current_user)]
    print(x)
    return flask.jsonify([c.get_data() for c in models.Convention.query.filter_by(user=flask_login.current_user)])


@api.blueprint.route("/conventions/<int:convention_key>")
def get_convention(convention_key):
    return flask.jsonify(_get_convention(convention_key).get_data())


@api.blueprint.route("/conventions/<int:convention_key>/validate/<s>")
def validate(convention_key, s):
    return flask.jsonify(_get_convention(convention_key).validate(s))


convention.app.register_blueprint(api.blueprint, url_prefix="/api")
