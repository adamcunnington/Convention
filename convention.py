import fnmatch
import re


class Pattern(object):
    def __init__(self, name, pattern, is_regex=False, allowable_values=None):
        self.name = name
        self.allowable_values = allowable_values or {}
        self.compiled_regex = re.compile(pattern if is_regex else fnmatch.translate(pattern))

    def validate(self, s):
        match = self.compiled_regex.match(s)
        if match is None:
            return False
        return all(value in self.allowable_values.get(key, (value)) for key, value in match.groupdict(default=True).items())
