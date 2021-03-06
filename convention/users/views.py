import flask
import flask_login

import convention
from convention import api, forms, models, users, utilities
from convention.api import views


@users.blueprint.route("/")
def index():
    api.before_request()
    conventions = views.get_conventions().response  # big problem with this is that this is a byte string, not the JSON object
    return flask.render_template("users.html", conventions=conventions)


@users.blueprint.route("/change-password", methods=("GET", "POST"))
def change_password():
    if not flask_login.current_user.registered:
        flask.flash("You must be a registered user to edit your profile.")
        return utilities.redirect()
    change_password_form = forms.ChangePasswordForm()
    if change_password_form.validate_on_submit():
        flask_login.current_user.password = change_password_form.password.data
        models.db.session.add(flask_login.current_user)
        models.db.session.commit()
        return utilities.redirect()
    return flask.render_template("form.html", title="Change Password", form=change_password_form)


@users.blueprint.route("/edit-profile", methods=("GET", "POST"))
def edit_profile():
    if not flask_login.current_user.registered:
        flask.flash("You must be a registered user to edit your profile.")
        return utilities.redirect()
    edit_profile_form = forms.EditProfileForm()
    if edit_profile_form.validate_on_submit():
        flask_login.current_user.first_name = edit_profile_form.first_name.data
        flask_login.current_user.last_name = edit_profile_form.last_name.data
        flask_login.current_user.avatar_url = edit_profile_form.avatar_url.data
        models.db.session.add(flask_login.current_user)
        models.db.session.commit()
        return utilities.redirect("users.edit_profile")
    edit_profile_form.first_name.data = flask_login.current_user.first_name
    edit_profile_form.last_name.data = flask_login.current_user.last_name
    edit_profile_form.avatar_url.data = flask_login.current_user.avatar_url
    return flask.render_template("form.html", title="Edit Profile", form=edit_profile_form)


convention.app.register_blueprint(users.blueprint, url_prefix="/users")
flask_login.login_manager.login_view = "users.index"
