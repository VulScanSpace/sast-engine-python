class ImportAccess(object):
    def __init__(self):
        self.path = None
        self.name = None
        self.alias = None

    def __init__(self, path, name, alias):
        self.path = path
        self.name = name
        self.alias = alias
