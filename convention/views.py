import flask
import flask_login

import convention
from convention import auth


@convention.app.route("/")
def index():
    return "Hello, World!"


@convention.app.route("/register")
def register():
    return flask.render_template("register.html")


@convention.app.route("/login")
def users():
    return flask.render_template("users.html")


@convention.app.route("/authorise/<provider>")
def authorise(provider):
    pass


@convention.app.route("/callback/<provider>")
def callback(provider):
    pass


@convention.app.route("/logout")
def logout_user():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("index"))


@auth.blueprint.route("/")
def auth_index():
    return "Welcome Back!"


convention.app.register_blueprint(auth.blueprint, url_prefix="/users")
