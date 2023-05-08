class SModule(object):
    def __init__(self, filename):
        self.filename = filename
        self.imports = dict()
        self.global_class_def = list()
        self.funcs = list()
        self.global_fields = dict()
        self.func_access = dict()
        self.expr = dict()

    def __str__(self) -> str:
        return ''
