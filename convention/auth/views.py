import flask
import flask_login

import convention
from convention import auth, forms, models, utilities


@auth.blueprint.route("/register", methods=("GET", "POST"))
def register():
    if flask_login.current_user.is_authenticated:
        flask.flash("You are already logged in.")
        return utilities.redirect()
    register_form = forms.RegisterForm()
    if register_form.validate_on_submit():
        if models.User.query.filter_by(email=register_form.email.data).first() is not None:
            flask.flash("That email is already registered.")
            return utilities.redirect("auth.register")
        user = models.User(email=register_form.email.data, password=register_form.password.data, first_name=register_form.first_name.data or None,
                           last_name=register_form.last_name.data or None, avatar_url=register_form.avatar_url.data or None)
        models.db.session.add(user)
        models.db.session.commit()
        flask_login.login_user(user, remember=True)
        return utilities.redirect("users.index")
    return flask.render_template("form.html", title="Register", form=register_form, submit_label="Register!")


@auth.blueprint.route("/login", methods=("GET", "POST"))  # need to check that next is not dodgy. Perhaps implement in utilities?
def login():
    if flask_login.current_user.is_authenticated:
        flask.flash("You are already logged in.")
        return utilities.redirect()
    login_form = forms.LoginForm()
    if login_form.validate_on_submit():
        user = models.User.query.filter_by(email=login_form.email.data).first()
        if user is None or not user.registered:
            flask.flash("That email is not registered.")
        else:
            if user.verify_password(login_form.password.data):
                flask_login.login_user(user, remember=True)
                return utilities.redirect()
            flask.flash("Invalid password.")
    return flask.render_template("form.html", title="Login", form=login_form, submit_label="Login!")


@auth.blueprint.route("/authorise/<provider>")
def authorise(provider):
    if not flask_login.current_user.is_anonymous:
        flask.flash("You are not an anonymous user.")
        return utilities.redirect()
    oauth_provider = auth.oauth_providers.get(provider)
    if oauth_provider is None:
        flask.abort(404)
    return oauth_provider.authorise()


@auth.blueprint.route("/callback/<provider>")
def callback(provider):
    if not flask_login.current_user.is_anonymous:
        flask.flash("You are not an anonymous user.")
        return utilities.redirect()
    user_info = auth.oauth_providers[provider].callback()
    if user_info is None:
        flask.flash("Authentication failed.")
        return utilities.redirect("auth.login")
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
    return utilities.redirect()


@auth.blueprint.route("/logout")
def logout():
    if not flask_login.current_user.is_authenticated:
        flask.flash("You are not logged in.")
    else:
        flask_login.logout_user()
    return utilities.redirect("index")


convention.app.register_blueprint(auth.blueprint, url_prefix="/auth")
