import flask

import convention


@convention.app.route("/")
def index():
    return flask.redirect(flask.url_for("auth.index"))
