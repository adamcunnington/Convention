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

    __tableargs__ = (db.UniqueConstraint(number, name), )


class AllowableValue(db.Model):
    __tablename__ = "AllowableValue"

    key = db.Column("AllowableValueKey", db.Integer, primary_key=True)
    name = db.Column("AllowableValueName", db.Unicode(100), unique=True)


class Convention(db.Model):
    __tablename__ = "Convention"

    key = db.Column("ConventionKey", db.Integer, primary_key=True)
    user_key = db.Column("UserKey", db.Integer, db.ForeignKey(User.key), nullable=False)
    name = db.Column("ConventionName", db.String(50), nullable=False)
    combinations_restricted = db.Column("ConventionCombinationsRestricted", db.Boolean, nullable=False)
    _is_regex = db.Column("ConventionIsRegex", db.Boolean)
    _pattern = db.Column("ConventionPattern", db.String(1000), nullable=False)

    user = db.relationship(User)
    restrictions = db.relationship(lambda: Restriction, lazy="dynamic", cascade="all, delete, delete-orphan")

    def __init__(self, name, user, pattern, is_regex, values=None, combinations=None, combinations_restricted=None):
        self.name = name
        self.user = user
        self.set_pattern(pattern, is_regex, values, combinations, combinations_restricted)

    @flask_sqlalchemy.orm.reconstructor
    def _init_on_load(self):
        self._regex = re.compile(fnmatch.translate(self._pattern) if not self._is_regex else self._pattern)

    def _add_restrictions(self, group_number, group_name, *values, combination_ID=None):
        for value in values:
            restriction = Restriction(combination_ID=combination_ID)
            restriction.allowable_value = db.session.query(AllowableValue).filter_by(name=value).first() or AllowableValue(name=value)
            restriction.allowable_group = (db.session.query(AllowableGroup).filter_by(number=group_number, name=group_name).first() or
                                           AllowableGroup(number=group_number, name=group_name))
            db.session.add(restriction.allowable_value)
            db.session.add(restriction.allowable_group)
            self.restrictions.append(restriction)

    @property
    def is_regex(self):
        return self._is_regex

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        raise AttributeError("The 'pattern' property is not directly writable. Please use the 'set_pattern' method instead.")

    def get_data(self):
        if self.combinations_restricted:
            allowables = collections.defaultdict(dict)
            # Despite combinations_restricted being True, we cannot assume that the restrictions will have a combination ID as the user could have
            # explicitly set combinations_restricted to True whilst restricting values only.
            for restriction in self.restrictions.filter(Restriction.combination_ID.isnot(None)):
                key = restriction.allowable_group.number + (" - " + restriction.allowable_group.name if restriction.allowable_group.name else "")
                allowables[restriction.combination_ID][key] = restriction.allowable_value.name
            label = "Allowable Combinations"
        else:
            allowables = collections.defaultdict(list)
            # Similar to the above scenario, we cannot assume that the combinations aren't restricted.
            for restriction in self.restrictions.filter(Restriction.combination_ID.is_(None)):
                key = restriction.allowable_group.number + (" - " + restriction.allowable_group.name if restriction.allowable_group.name else "")
                allowables[key].append(restriction.allowable_value.name)
            label = "Allowable Values"
        return {
            Convention.key.name: str(self.key),
            User.email.name: self.user.email,
            Convention.name.name: self.name,
            Convention._pattern.name: self._pattern,
            Convention.combinations_restricted.name: self.combinations_restricted,
            label: allowables
        }

    def set_restrictions(self, values=None, combinations=None, combinations_restricted=None):
        pattern_named_groups = self._regex.groupindex.items()
        group_names = {v: k for k, v in pattern_named_groups}  # Reverse the groupindex mapping
        if values is not None:
            if combinations is not None:
                raise ConventionException("The 'values' and 'combinations' parameters cannot both be provided")
            # The user has provided new values so we need to check that they fit the pattern structure.
            if len(values) > self._regex.groups:
                raise ConventionException("More groups of allowable values were provided than capturing groups in the pattern.")
            self.restrictions = []  # New values overwrite existing restrictions
            for index, values in enumerate(values):
                group_number = index + 1
                self._add_restrictions(group_number, group_names.get(group_number), *values)
            self.combinations_restricted = False
            return
        elif combinations is None:
            if self.restrictions is not None:
                # The user has not provided any new values or combinations but we need to ensure that any existing restrictions fit the new pattern.
                # Specifically, we check that the existing named groups still feature in the new pattern, and with the same group index.
                if all(row in pattern_named_groups for row in self.restrictions.join(Restriction.allowable_group).filter(
                        AllowableGroup.name.isnot(None)).distinct(AllowableGroup.name, AllowableGroup.number).with_entities(
                        AllowableGroup.name, AllowableGroup.number)):
                    # Unnamed groups will not be accounted for in the above so we also need to find out the total number of groups that are currently
                    # restricted so we can check that the new pattern doesn't contain fewer groups. The max is sufficient for value-only restrictions
                    # and for combinations, this is sufficient also as combinations entail restrictions for every group in the pattern.
                    group_count = self.restrictions.join(Restriction.allowable_group).with_entities(db.func.max(AllowableGroup.number)).scalar()
                    # The combinations_restricted flag is not necessarily indicative of whether combinations are restricted as the user could have
                    # explicitly toggled this value. We can just check whether the combination_ID is nullable from the first arbitrary row as it is
                    # not possible to mix value-only and combination restrictions.
                    combinations_exist = self.restrictions.first().combination_ID is not None
                    if ((combinations_exist and group_count == self._regex.groups) or (not combinations_exist and group_count <= self._regex.groups)):
                        return
                raise ConventionException("The changes to the pattern break the restrictions. Please provide new restrictions to 'set_pattern'.")
            return
        group_count = len(combinations[0])
        if not all(len(combination) == group_count for combination in combinations):
            raise ConventionException("The number of groups were inconsistent amongst the combinations.")
        if group_count != self._regex.groups:
            raise ConventionException("The number of groups in the combinations was different to the number of capturing groups in the pattern.")
        self.restrictions = []  # New combinations overwrite existing restrictions
        for combination_index, combination in enumerate(combinations):
            for index, value in enumerate(combination):
                group_number = index + 1
                self._add_restrictions(group_number, group_names.get(group_number), value, combination_ID=combination_index + 1)
        self.combinations_restricted = True if combinations_restricted is None else combinations_restricted

    def set_pattern(self, pattern, is_regex, values=None, combinations=None, combinations_restricted=None):
        self._pattern = pattern
        self._is_regex = is_regex
        self._init_on_load()
        if is_regex:
            self.set_restrictions(values, combinations, combinations_restricted)
        else:
            # The user has explicitly opted for the basic wildcard pattern which does not support capturing groups so any existing restrictions can
            # be forgotten.
            self.restrictions = []
            self.combinations_restricted = False

    def validate(self, s):
        match = self._regex.match(s)
        if match is None:
            return False
        # We know that the input matches the pattern but we now need to test that any values passed to capturing groups are allowable.
        groups = match.groups()
        if self.combinations_restricted:
            combination_IDs = collections.Counter()
            for index in range(self._regex.groups):
                group_number = index + 1
                value = groups[group_number] or None
                # For each value captured by a group, we look for combination IDs that allow that value and add them to a counter object which will
                # keep track of the amount of times that combination ID has occured.
                combination_IDs.update(self.restrictions.join(Restriction.allowable_value, Restriction.allowable_group)
                                       .filter(AllowableGroup.number == group_number, AllowableValue.name == value)
                                       .with_entities(Restriction.combination_ID).all())
            # We then take the combination_ID that occured most and see if the number of occurences matches the number of capturing groups in the
            # pattern. If so, we know that all the captured values were a valid combination.
            return (0 if not combination_IDs else combination_IDs.most_common(1)[0][1]) == len(groups)
        if self.restrictions is not None:
            for index in range(self._regex.groups):
                group_number = index + 1
                value = groups[group_number] or None
                # In the case of value-only restrictions, we need to check that the captured value is valid, but only if the group itself is
                # restricted. We determine this by looking to see if there is at least one restriction for the group.
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
