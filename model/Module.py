class SModule(object):
    def __init__(self):
        self.imports = dict()
        self.classs = dict()
        self.funcs = dict()
        self.fields = dict()
        self.func_access = dict()
        self.expr = dict()

    def __str__(self) -> str:
        return ''
