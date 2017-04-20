import flask_wtf
import wtforms
from wtforms import validators


class _PasswordField(object):
    password = wtforms.PasswordField("Password", validators=(validators.DataRequired(), ))


class _EmailField(object):
    email = wtforms.StringField("Email", validators=(validators.DataRequired(), validators.Email(), validators.Length(max=320)))


class _EditableFields(object):
    first_name = wtforms.StringField("First Name", validators=(validators.Length(max=35), ))
    last_name = wtforms.StringField("Last Name", validators=(validators.Length(max=35), ))
    avatar_url = wtforms.StringField("Avatar URL", validators=(validators.URL, validators.Length(max=500)))


class RegisterForm(flask_wtf.FlaskForm, _PasswordField, _EmailField, _EditableFields):
    pass


class LoginForm(flask_wtf.FlaskForm, _PasswordField, _EmailField):
    pass


class ChangePasswordForm(flask_wtf.FlaskForm, _PasswordField):
    pass


class EditProfileForm(flask_wtf.FlaskForm, _EditableFields):
    pass
