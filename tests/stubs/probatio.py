class Schema:
    def __init__(self, s):
        self.schema = s


class Required(str):
    def __new__(cls, k, default=None):
        key = str.__new__(cls, k)
        key.default = default
        return key


def Match(p):
    return str


def All(*a):
    return str


Strip = object()


class Optional(Required):
    pass
