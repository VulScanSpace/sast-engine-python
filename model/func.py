from model import AstModel


class SFuncDef(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.name = ''
        self.annotations = list()
        self.args = list()
        self.rets = list()
        self.local_vars = list()
        self.func_accesses = list()
        self.body_array = list()

    def __str__(self) -> str:
        return self.name

    def set_name(self, name: str):
        self.name = name

    def get_name(self):
        return self.name

    def add_annotation(self, annotation):
        self.annotations.append(annotation)

    def set_args(self, args):
        self.args = args

    def add_ret(self, ret):
        self.rets.append(ret)

    def add_body(self, body):
        self.body_array.append(body)

    def add_local_var(self, _local_var):
        self.local_vars.append(_local_var)

    def add_func_access(self, _func_access):
        self.func_accesses.append(_func_access)
