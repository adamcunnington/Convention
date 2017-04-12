import fnmatch
import re

import flask_sqlalchemy

import convention


db = flask_sqlalchemy.SQLAlchemy(convention.app)


allowables = db.Table("convention_allowable_value",
                      db.Column("convention_key", db.Integer, db.ForeignKey("convention.convention_key")),
                      db.Column("allowable_value_key", db.Integer, db.ForeignKey("allowable_value.allowable_value_key")),
                      db.PrimaryKeyConstraint("convention_key", "allowable_value_key"))


class Convention(db.Model):
    __tablename__ = "convention"

    convention_key = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    pattern = db.Column(db.String(255), nullable=False)
    allowable_values = db.relationship("AllowableValue", secondary=allowables)

    def __init__(self, name, pattern, is_regex=False, allowable_values=None):
        self.name = name
        self.pattern = pattern if is_regex else fnmatch.translate(pattern)
        self._allowable_values = allowable_values or {}
        for key, values in self._allowable_values.items():
            for value in values:
                self.allowable_values.append(AllowableValue.query.filter_by(group_name=key, value=value).first() or AllowableValue(key, value))
        self._compiled_regex = re.compile(self.pattern)

    def validate(self, s):
        match = self._compiled_regex.match(s)
        if match is None:
            return False
        return all(value in self._allowable_values.get(key, (value)) for key, value in match.groupdict(default=True).items())


class AllowableValue(db.Model):
    __tablename__ = "allowable_value"

    allowable_value_key = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    __table_args__ = db.UniqueConstraint("group_name", "value")

    def __init__(self, value):
        self.value = value
