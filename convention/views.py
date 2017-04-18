import flask
import flask_login

import convention
from convention import auth, models


@convention.app.route("/")
def index():
    return "Hello, World!"


@convention.app.route("/register")
def register():
    if flask_login.current_user.is_authenticated:
        flask.flash("You are already registered and logged in.")
        return flask.redirect(flask.url_for("auth.users_index"))
    return flask.render_template("register.html")


@convention.app.route("/login")
def login():
    if flask_login.current_user.is_authenticated:
        flask.flash("You are already registered and logged in.")
        return flask.redirect(flask.url_for("auth.users_index"))
    return flask.render_template("users.html")


@convention.app.route("/login-form")
def login_form():
    if flask_login.current_user.is_authenticated:
        flask.flash("You are already registered and logged in.")
        return flask.redirect(flask.url_for("auth.users_index"))
    return flask.render_template("login.html")


@convention.app.route("/authorise/<provider>")
def authorise(provider):
    if not flask_login.current_user.is_anonymous:
        flask.flash("You are not an anonymous user.")
        return flask.redirect(flask.url_for("auth.users_index"))
    return auth.oauth_providers[provider].authorise()


@convention.app.route("/callback/<provider>")
def callback(provider):
    if not flask_login.current_user.is_anonymous:
        flask.flash("You are not an anonymous user.")
        return flask.redirect(flask.url_for("auth.users_index"))
    user_info = auth.oauth_providers[provider].callback()
    if user_info is None:
        flask.flash("Authentication failed.")
        return flask.redirect(flask.url_for("login"))
    user = models.User.query.filter_by().first()
    if user is None:
        user = models.User(**user_info)
    else:
        user.email = user_info.get("email", user.email)
        user.first_name = user_info.get("first_name", user.first_name)
        user.last_name = user_info.get("last_name", user.last_name)
        user.avatar_url = user_info.get("avatar_url", user.avatar_url)
    models.db.session.add(user)
    models.db.session.commit()
    flask_login.login_user(user, remember=True)
    return flask.redirect(flask.url_for("auth.users_index"))


@convention.app.route("/logout")
def logout_user():
    if not flask_login.current_user.is_authenticated:
        flask.flash("You are not logged in.")
        return flask.redirect(flask.url_for("index"))
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login"))


@auth.blueprint.route("/")
def users_index():
    return "Welcome Back!"


convention.app.register_blueprint(auth.blueprint, url_prefix="/users")
