import collections
import fnmatch
import re

import flask_sqlalchemy

import convention


convention.app.config["SQLALCHEMY_DATABASE_URI"] = r"sqlite:///C:\Python Projects\Convention\convention.db"
db = flask_sqlalchemy.SQLAlchemy(convention.app)


allowables = db.Table("Convention_AllowableValue",
                      db.Column("ConventionKey", db.Integer, db.ForeignKey("Convention.ConventionKey")),
                      db.Column("AllowableValueKey", db.Integer, db.ForeignKey("AllowableValue.AllowableValueKey")),
                      db.PrimaryKeyConstraint("ConventionKey", "AllowableValueKey"))


class Convention(db.Model):
    __tablename__ = "Convention"

    convention_key = db.Column("ConventionKey", db.Integer, primary_key=True)
    name = db.Column("ConventionName", db.String(50), unique=True, nullable=False)
    _pattern = db.Column("ConventionPattern", db.String(255), nullable=False)
    allowable_values = db.relationship("AllowableValue", secondary=allowables, lazy="dynamic")

    def __init__(self, name, pattern, is_regex=False, allowable_values=None):
        self.name = name
        if allowable_values is not None:
            for group, names in allowable_values.items():
                for name in names:
                    self.allowable_values.append(AllowableValue.query.filter_by(group=group, name=name).first() or AllowableValue(group, name))
        self.set_pattern(pattern, is_regex)

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
        allowable_values = collections.defaultdict(list)
        for allowable_value in self.allowable_values:
            allowable_values[allowable_value.group].append(allowable_value.name)
        return {
            Convention.convention_key.name: self.convention_key,
            Convention.name.name: self.name,
            Convention._pattern.name: self._pattern,
            "Allowable Values": allowable_values
        }

    def set_pattern(self, pattern, is_regex=False):
        self._pattern = pattern if is_regex else fnmatch.translate(pattern)
        self._init_on_load()

    def validate(self, s):
        match = self._compiled_regex.match(s)
        if match is None:
            return False
        for group, name in match.groupdict().items():
            if (name is not None and self.allowable_values.filter_by(group=group).first() is not None and
                    self.allowable_values.filter_by(group=group, name=name).first() is None):
                return False
        return True


class AllowableValue(db.Model):
    __tablename__ = "AllowableValue"

    allowable_value_key = db.Column("AllowableValueKey", db.Integer, primary_key=True)
    group = db.Column("AllowableValueGroup", db.String(50), nullable=False)
    name = db.Column("AllowableValueName", db.String(100), nullable=False)

    __table_args__ = (db.UniqueConstraint("AllowableValueGroup", "AllowableValueName"), )

    def __init__(self, group, name):
        self.group = group
        self.name = name
