import collections
import datetime
import fnmatch
import re

from werkzeug import security
import flask_login
import flask_sqlalchemy
import itsdangerous

import convention


_SECRET_KEY = convention.app.config["SECRET_KEY"]

db = flask_sqlalchemy.SQLAlchemy(convention.app)


class ConventionException(Exception):
    pass


class User(db.Model, flask_login.UserMixin):
    __tablename__ = "User"

    key = db.Column("UserKey", db.Integer, primary_key=True)
    email = db.Column("UserEmail", db.Unicode(320), index=True, unique=True, nullable=False)
    created_on_utc = db.Column("UserCreatedOnUTC", db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_updated_utc = db.Column("UserLastUpdatedUTC", db.DateTime, default=datetime.datetime.utcnow,
                                 onupdate=datetime.datetime.utcnow, nullable=False)
    password_hash = db.Column("UserPasswordHash", db.Unicode(128))
    first_name = db.Column("UserFirstName", db.Unicode(35))
    last_name = db.Column("UserLastName", db.Unicode(35))
    avatar_url = db.Column("UserAvatarURL", db.Unicode(500))
    is_active = db.Column("UserIsActive", db.Boolean, default=True)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password):
        self.password_hash = security.generate_password_hash(password)

    @property
    def registered(self):
        return self.password_hash is not None

    @staticmethod
    def verify_auth_token(token):
        serialiser = itsdangerous.TimedJSONWebSignatureSerializer(_SECRET_KEY)
        try:
            data = serialiser.loads(token)
        except (itsdangerous.BadSignature, itsdangerous.SignatureExpired):
            return None
        return User.query.get(data["UserKey"])

    def generate_auth_token(self, expires_in=3600):
        serialiser = itsdangerous.TimedJSONWebSignatureSerializer(_SECRET_KEY, expires_in=expires_in)
        return serialiser.dumps({"UserKey": self.key}).decode("UTF-8")

    def get_id(self):
        return self.key

    def verify_password(self, password):
        return security.check_password_hash(self.password_hash, password)


class AllowableGroup(db.Model):
    __tablename__ = "AllowableGroup"

    key = db.Column("AllowableGroupKey", db.Integer, primary_key=True)
    number = db.Column("AllowableGroupNumber", db.Integer, nullable=False)
    name = db.Column("AllowableGroupName", db.Unicode(50))

    __tableargs__ = (db.UniqueConstraint("AllowableGroupNumber", "AllowableGroupName"), )


class AllowableValue(db.Model):
    __tablename__ = "AllowableValue"

    key = db.Column("AllowableValueKey", db.Integer, primary_key=True)
    name = db.Column("AllowableValueName", db.Unicode(100), unique=True, nullable=False)


class Convention(db.Model):
    __tablename__ = "Convention"

    key = db.Column("ConventionKey", db.Integer, primary_key=True)
    user_key = db.Column("UserKey", db.Integer, db.ForeignKey(User.key), nullable=False)
    name = db.Column("ConventionName", db.Unicode(50), nullable=False)
    combinations_restricted = db.Column("ConventionCombinationsRestricted", db.Boolean, nullable=False)
    _pattern = db.Column("ConventionPattern", db.Unicode(1000), nullable=False)

    user = db.relationship(User)
    restrictions = db.relationship(lambda: Restriction, lazy="dynamic", cascade="all, delete, delete-orphan")

    __tableargs__ = (db.UniqueConstraint(user_key, name), )

    def __init__(self, name, user, pattern, is_regex=False, allowable_values=None, allowable_combinations=None):
        self.name = name
        self.user = user
        self.set_pattern(pattern, is_regex, allowable_values, allowable_combinations)

    def _add_allowable_values(self, group_number, group_name, *values, combination_ID=None):
        for value in values:
            restriction = Restriction(group_number=group_number, group_name=group_name, combination_ID=combination_ID)
            restriction.allowable_value = db.session.query(AllowableValue).filter_by(name=value).first() or AllowableValue(value)
            db.session.add(restriction.allowable_value)
            self.restrictions.append(restriction)

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
            allowables = collections.defaultdict(dict)
            for restriction in self.restrictions.filter(Restriction.combination_ID.isnot(None)):
                allowables[restriction.combination_ID][restriction.allowable_group.name or
                                                       str(restriction.allowable_group.number)] = restriction.allowable_value.name
            label = "Allowable Combinations"
        else:
            allowables = collections.defaultdict(list)
            for restriction in self.restriction.filter(Restriction.combination_ID.is_(None)):
                allowables[restriction.allowable_group.name or str(restriction.allowable_group.number)].append(restriction.allowable_value.name)
            label = "Allowable Values"
        return {
            Convention.key.name: str(self.key),
            User.email.name: self.user.email,
            Convention.name.name: self.name,
            Convention._pattern.name: self._pattern,
            Convention.combinations_restricted.name: self.combinations_restricted,
            label: allowables
        }

    def set_pattern(self, pattern, is_regex=False, allowable_values=None, allowable_combinations=None):
        self._pattern = pattern if is_regex else fnmatch.translate(pattern)
        self.combinations_restricted = is_regex and bool(allowable_combinations is not None or self.combinations_restricted)
        self._init_on_load()
        if is_regex and (allowable_values and allowable_combinations):
            raise ConventionException("Only one of allowable_values and allowable_combinations can be provided.")
        if self.restrictions.first() is not None:
            if not is_regex or (allowable_values or allowable_combinations):
                self.restrictions = []
            else:
                if self.restrictions.join(Restriction.allowable_group).with_entities(
                        db.func.max(AllowableGroup.number)).scalar() > self._compiled_regex.groups:
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
                combination_IDs.update(self.restrictions.join(Restriction.allowable_value, Restriction.allowable_group)
                                       .filter(AllowableGroup.number == index + 1, AllowableValue.name == value)
                                       .with_entities(Restriction.combination_ID).all())
            return (0 if not combination_IDs else combination_IDs.most_common(1)[0][1]) == len(groups)
        if self.restrictions is not None:
            for index, value in enumerate(groups):
                group_number = index + 1
                if (self.restrictions.join(Restriction.allowable_group).filter(AllowableGroup.number == group_number).first()
                        is not None and self.restrictions.join(Restriction.allowable_group, Restriction.allowable_value)
                        .filter(AllowableGroup.number == group_number, AllowableValue.name == value).first() is None):
                    return False
        return True


class Restriction(db.Model):
    __tablename__ = "Restriction"

    key = db.Column("RestrictionKey", db.Integer, primary_key=True)
    convention_key = db.Column("ConventionKey", db.Integer, db.ForeignKey(Convention.key), nullable=False)
    allowable_value_key = db.Column("AllowableValueKey", db.Integer, db.ForeignKey(AllowableValue.key), nullable=False)
    allowable_group_key = db.Column("AllowableGroupKey", db.Integer, db.ForeignKey(AllowableGroup.key), nullable=False)
    combination_ID = db.Column("AllowableCombinationID", db.Integer)

    allowable_value = db.relationship(AllowableValue)
    allowable_group = db.relationship(AllowableGroup)

    __tableargs__ = (db.UniqueConstraint(key, allowable_value_key, allowable_group_key, combination_ID), )
