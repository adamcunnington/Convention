import flask

import convention
from convention import api, decorators, models


def _get_convention(convention_key):
    c = models.Convention.query.get_or_404(convention_key).first()
    if c.user != flask.g.current_user:
        flask.abort(401)
    return c


def _get_convention_url(convention_key):
    return flask.url_for("api.get_convention", convention_key=convention_key, _external=True)


@api.blueprint.route("/conventions/")
@decorators.add_etag
@decorators.to_json
@decorators.add_collection_controls("api.get_convention", "convention_key")
def get_conventions():
    return models.Convention.query.filter_by(user=flask.g.current_user)


@api.blueprint.route("/conventions/", methods=["POST"])
@decorators.to_json
def add_convention():
    data = flask.request.get_json(force=True)
    c = models.Convention(data["name"], flask.g.current_user, data["pattern"], data.get("is_regex", False), data.get("values"),
                          data.get("combinations"), data.get("combinations_restricted"))
    models.db.session.add(c)
    models.db.session.commit()
    return {}, 201, {"Location": _get_convention_url(c.key)}


@api.blueprint.route("/conventions/<int:convention_key>")
@decorators.add_etag
@decorators.to_json
def get_convention(convention_key):
    return _get_convention(convention_key).get_data()


@api.blueprint.route("/conventions/<int:convention_key>", methods=["DELETE"])
@decorators.to_json
def delete_convention(convention_key):
    models.db.session.delete(_get_convention(convention_key))
    models.db.session.commit()
    return


@api.blueprint.route("/conventions/<int:convention_key>/validate/<s>")
@decorators.add_etag
@decorators.to_json
def validate(convention_key, s):
    return _get_convention(convention_key).validate(s)


convention.app.register_blueprint(api.blueprint, url_prefix="/api")
