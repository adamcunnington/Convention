import flask_wtf
import wtforms
from wtforms import validators


class LoginForm(flask_wtf.Form):
    email = wtforms.StringField("email", validators=(validators.DataRequired(), validators.Email(), validators.Length(max=320)))
    password = wtforms.PasswordField("password", validators=(validators.DataRequired()))


class RegisterForm(LoginForm):
    first_name = wtforms.StringField("first_name", validators=(validators.Length(max=35), ))
    last_name = wtforms.StringField("last_name", validators=(validators.Length(max=35), ))
    avatar_url = wtforms.StringField("avatar_url", validators=(validators.URL, validators.Length(max=500)))
