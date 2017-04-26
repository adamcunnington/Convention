import collections
import datetime
import fnmatch
import re

from werkzeug import security
import flask
import flask_login
import flask_sqlalchemy
import itsdangerous

import convention


db = flask_sqlalchemy.SQLAlchemy(convention.app)


class ConventionException(Exception):
    pass


class Convention_AllowableValue(db.Model):
    __tablename__ = "Convention_AllowableValue"

    key = db.Column("Convention_AllowableValueKey", db.Integer, primary_key=True)
    convention_key = db.Column("ConventionKey", db.Integer, db.ForeignKey("Convention.ConventionKey"), nullable=False)
    allowable_value_key = db.Column("AllowableValueKey", db.Integer, db.ForeignKey("AllowableValue.AllowableValueKey"), nullable=False)
    group_name = db.Column("AllowableValueGroupName", db.String(50))
    group_number = db.Column("AllowableValueGroupNumber", db.SmallInteger, nullable=False)
    combination_ID = db.Column("AllowableValueCombinationID", db.Integer)
    allowable_value = db.relationship("AllowableValue")

    __tableargs__ = (db.UniqueConstraint("ConventionKey", "AllowableValueKey", "AllowableValueGroupNumber", "AllowableValueCombinationID"), )


class AllowableValue(db.Model):
    __tablename__ = "AllowableValue"

    key = db.Column("AllowableValueKey", db.Integer, primary_key=True)
    name = db.Column("AllowableValueName", db.String(100), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name


class Convention(db.Model):
    __tablename__ = "Convention"

    key = db.Column("ConventionKey", db.Integer, primary_key=True)
    user_key = db.Column("UserKey", db.Integer, db.ForeignKey("User.UserKey"), nullable=False)
    name = db.Column("ConventionName", db.String(50), nullable=False)
    _pattern = db.Column("ConventionPattern", db.String(1000), nullable=False)
    combinations_restricted = db.Column("ConventionCombinationsRestricted", db.Boolean, nullable=False)
    user = db.relationship("User")
    allowable_values = db.relationship("Convention_AllowableValue", lazy="dynamic", cascade="all, delete, delete-orphan")  # cascade options required?

    __tableargs__ = (db.UniqueConstraint("UserKey", "ConventionName"), )

    def __init__(self, name, user, pattern, is_regex=False, allowable_values=None, allowable_combinations=None):
        self.name = name
        self.user = user
        self.set_pattern(pattern, is_regex, allowable_values, allowable_combinations)

    def _add_allowable_values(self, group_number, group_name, *values, combination_ID=None):
        for value in values:
            association = Convention_AllowableValue(group_number=group_number, group_name=group_name, combination_ID=combination_ID)
            association.allowable_value = db.session.query(AllowableValue).filter_by(name=value).first() or AllowableValue(value)
            db.session.add(association.allowable_value)
            self.allowable_values.append(association)

    @flask_sqlalchemy.orm.reconstructor
    def _init_on_load(self):
        self._compiled_regex = re.compile(self.pattern)

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        raise AttributeError("pattern is not directly writeable. Use set_pattern instead.")

    def get_data(self):
        if self.combinations_restricted:
            allowable_values = collections.defaultdict(dict)
            for allowable_value in self.allowable_values.filter(Convention_AllowableValue.combination_ID.isnot(None)):
                allowable_values[allowable_value.combination_ID][allowable_value.group_name or
                                                                 str(allowable_value.group_number)] = allowable_value.allowable_value.name
            allowable_values = list(allowable_values.values())
            label = "Allowable Combinations"
        else:
            allowable_values = collections.defaultdict(list)
            for allowable_value in self.allowable_values.filter(Convention_AllowableValue.combination_ID.is_(None)):
                allowable_values[allowable_value.group_name or str(allowable_value.group_number)].append(allowable_value.allowable_value.name)
            label = "Allowable Values"
        return {
            Convention.key.name: str(self.key),
            User.email.name: self.user.email,
            Convention.name.name: self.name,
            Convention._pattern.name: self._pattern,
            Convention.combinations_restricted.name: self.combinations_restricted,
            label: allowable_values
        }

    def get_url(self):
        return flask.url_for("api.get_convention", convention_key=self.key, _external=True)

    def set_pattern(self, pattern, is_regex=False, allowable_values=None, allowable_combinations=None):
        self._pattern = pattern if is_regex else fnmatch.translate(pattern)
        self.combinations_restricted = is_regex and bool(allowable_combinations is not None or self.combinations_restricted)
        self._init_on_load()
        if is_regex and (allowable_values and allowable_combinations):
            raise ConventionException("Only one of allowable_values and allowable_combinations can be provided.")
        if self.allowable_values.first() is not None:
            if not is_regex or (allowable_values or allowable_combinations):
                self.allowable_values = []
            else:
                if self.allowable_values.with_entities(db.func.max(Convention_AllowableValue.group_number)).scalar() > self._compiled_regex.groups:
                    raise ConventionException("After updating the pattern, there are more groups of allowable values than capturing groups defined " +
                                              "in the pattern. Please pass allowable_values or allowable_combinations when updating the pattern")
                return
        if is_regex:
            group_names = {v: k for k, v in self._compiled_regex.groupindex.items()}
            if allowable_values is not None:
                if len(allowable_values) > self._compiled_regex.groups:
                    raise ConventionException("There are more groups of allowable values than capturing groups defined in the pattern.")
                for index, values in enumerate(allowable_values):
                    group_number = index + 1
                    self._add_allowable_values(group_number, group_names.get(group_number), *values)
            elif allowable_combinations is not None:
                if len(allowable_combinations[0]) != self._compiled_regex.groups:
                    raise ConventionException("The number of groups in the allowable combinations is different to the number of capturing groups " +
                                              "defined in the pattern.")
                for combination_ID, allowable_combination in enumerate(allowable_combinations):
                    for index, value in enumerate(allowable_combination):
                        group_number = index + 1
                        self._add_allowable_values(group_number, group_names.get(group_number), value, combination_ID=combination_ID + 1)

    def validate(self, s):
        match = self._compiled_regex.match(s)
        if match is None:
            return False
        groups = match.groups()
        if self.combinations_restricted:
            combination_IDs = collections.Counter()
            for index, value in enumerate(groups):
                combination_IDs.update(self.allowable_values.join(Convention_AllowableValue.allowable_value).filter(
                    Convention_AllowableValue.group_number == index + 1,
                    AllowableValue.name == value).with_entities(Convention_AllowableValue.combination_ID).all())
            return (0 if not combination_IDs else combination_IDs.most_common(1)[0][1]) == len(groups)
        if self.allowable_values is not None:
            for index, value in enumerate(groups):
                group_number = index + 1
                if (self.allowable_values.filter_by(group_number=group_number).first() is not None and
                        self.allowable_values.join(Convention_AllowableValue.allowable_value).filter(
                        Convention_AllowableValue.group_number == group_number, AllowableValue.name == value).first() is None):
                    return False
        return True


class User(db.Model, flask_login.UserMixin):
    __tablename__ = "User"

    key = db.Column("UserKey", db.Integer, primary_key=True)
    email = db.Column("UserEmail", db.String(320), index=True, unique=True, nullable=False)
    password_hash = db.Column("UserPasswordHash", db.String(128))
    first_name = db.Column("UserFirstName", db.String(35))
    last_name = db.Column("UserLastName", db.String(35))
    avatar_url = db.Column("UserAvatarURL", db.String(500))
    is_active = db.Column("UserIsActive", db.Boolean, default=True)
    created_on_utc = db.Column("UserCreatedOnUTC", db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_updated_utc = db.Column("UserLastUpdatedUTC", db.DateTime, default=datetime.datetime.utcnow,
                                 onupdate=datetime.datetime.utcnow, nullable=False)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = security.generate_password_hash(password)

    @property
    def registered(self):
        return self.password_hash is not None

    @staticmethod
    def verify_auth_token(token):
        serialiser = itsdangerous.TimedJSONWebSignatureSerializer(convention.app.config["SECRET_KEY"])
        try:
            data = serialiser.loads(token)
        except (itsdangerous.BadSignature, itsdangerous.SignatureExpired):
            return None
        return User.query.get(data["UserKey"])

    def generate_auth_token(self, expires_in=3600):
        serialiser = itsdangerous.TimedJSONWebSignatureSerializer(convention.app.config["SECRET_KEY"], expires_in=expires_in)
        return serialiser.dumps({"UserKey": self.key}).decode("UTF-8")

    def get_id(self):
        return self.key

    def verify_password(self, password):
        return security.check_password_hash(self.password_hash, password)
