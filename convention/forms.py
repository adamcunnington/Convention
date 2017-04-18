import flask_wtf
import wtforms
from wtforms import validators


class _PasswordField(object):
    password = wtforms.PasswordField("password", validators=(validators.DataRequired()))


class _EmailField(object):
    email = wtforms.StringField("email", validators=(validators.DataRequired(), validators.Email(), validators.Length(max=320)))


class _EditableFields(object):
    first_name = wtforms.StringField("first_name", validators=(validators.Length(max=35), ))
    last_name = wtforms.StringField("last_name", validators=(validators.Length(max=35), ))
    avatar_url = wtforms.StringField("avatar_url", validators=(validators.URL, validators.Length(max=500)))


class RegisterForm(flask_wtf.Form, _PasswordField, _EmailField, _EditableFields):
    pass


class LoginForm(flask_wtf.Form, _PasswordField, _EmailField):
    pass


class EditProfileForm(flask_wtf.Form, _EditableFields, _PasswordField):
    pass
