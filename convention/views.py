import flask
import flask_login

import convention
from convention import auth, forms, models


@convention.app.route("/")
def index():
    return "Hello, World!"


@convention.app.route("/register", methods=("GET", "POST"))
def register():
    if flask_login.current_user.is_authenticated:
        flask.flash("You are already logged in.")
        return flask.redirect(flask.url_for("auth.users_index"))
    register_form = forms.RegisterForm()
    if register_form.validate_on_submit():
        if models.User.query.filter_by(email=register_form.email.data).first() is not None:
            flask.flash("That email is already registered.")
            return flask.redirect(flask.url_for("register"))
        user = models.User(**register_form.data)
        models.db.session.add(user)
        models.db.session.commit()
        flask_login.login_user(user, remember=True)
        return flask.redirect(flask.url_for("auth.users_index"))
    return flask.render_template("register.html", form=register_form)


@convention.app.route("/users")
def users():
    return flask.render_template("users.html")


@convention.app.route("/login", methods=("GET", "POST"))
def login():
    if flask_login.current_user.is_authenticated:
        flask.flash("You are already logged in.")
        return flask.redirect(flask.url_for("auth.users_index"))
    login_form = forms.LoginForm()
    if login_form.validate_on_submit():
        user = models.User.query.filter_by(email=login_form.email.data).first()
        if user is None:
            flask.flash("That email is not registered.")
        else:
            if user.verify_password(login_form.password.data):
                flask_login.login_user(user, remember=True)
                return flask.redirect(flask.url_for("auth.users_index"))
            flask.flash("Invalid password.")
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
        return flask.redirect(flask.url_for("users"))
    email = user_info["email"]
    user = models.User.query.filter_by(email=email).first()
    if user is None:
        user = models.User(**user_info)
    else:
        user.email = email
        user.first_name = user_info.get("first_name", user.first_name)
        user.last_name = user_info.get("last_name", user.last_name)
        user.avatar_url = user_info.get("avatar_url", user.avatar_url)
    models.db.session.add(user)
    models.db.session.commit()
    flask_login.login_user(user, remember=True)
    return flask.redirect(flask.url_for("auth.users_index"))


@convention.app.route("/logout")
def logout():
    if not flask_login.current_user.is_authenticated:
        flask.flash("You are not logged in.")
        return flask.redirect(flask.url_for("index"))
    flask_login.logout_user()
    return flask.redirect(flask.url_for("users"))


@auth.blueprint.route("/")
def users_index():
    return "Welcome Back!"


@auth.blueprint.route("/change-password", methods=("GET", "POST"))
def change_password():
    if not flask_login.current_user.registered:
        flask.flash("You must be a registered user to edit your profile.")
        return flask.redirect(flask.url_for("auth.users_index"))
    change_password_form = forms.ChangePasswordForm()
    if change_password_form.validate_on_submit():
        flask_login.current_user.password = change_password_form.password.data
        models.db.session.add(flask_login.current_user)
        models.db.session.commit()
        return flask.redirect(flask.url_for("auth.users_index"))
    return flask.render_template("edit-profile.html", form=change_password_form)


@auth.blueprint.route("/edit-profile", methods=("GET", "POST"))
def edit_profile():
    if not flask_login.current_user.registered:
        flask.flash("You must be a registered user to edit your profile.")
        return flask.redirect(flask.url_for("auth.users_index"))
    edit_profile_form = forms.EditProfileForm()
    if edit_profile_form.validate_on_submit():
        flask_login.current_user.first_name = edit_profile_form.first_name.data
        flask_login.current_user.last_name = edit_profile_form.last_name.data
        flask_login.current_user.avatar_url = edit_profile_form.avatar_url.data
        models.db.session.add(flask_login.current_user)
        models.db.session.commit()
        return flask.redirect(flask.url_for("auth.users_index"))
    edit_profile_form.first_name.data = flask_login.current_user.first_name
    edit_profile_form.last_name.data = flask_login.current_user.last_name
    edit_profile_form.avatar_url.data = flask_login.current_user.avatar_url
    return flask.render_template("edit-profile.html", form=edit_profile_form)


convention.app.register_blueprint(auth.blueprint, url_prefix="/users")
