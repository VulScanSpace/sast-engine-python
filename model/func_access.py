import ast

from model import AstModel
from model.func import SFuncDef


class FuncAccess(AstModel):
    expr = None
    var_access = None
    name = None
    object_class = None
    label = None
    args = None
    parent = None
    node = None

    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.args = list()
        self.label = str()
        self.name = str()
        self.expr = str()
        # self.parent = SFuncDef()

    def __str__(self) -> str:
        _expr = str(self.var_access)
        _expr = _expr + '('
        if len(self.args) > 0:
            _expr = _expr + ', '.join([str(_) for _ in self.args])
        _expr = _expr + ')'
        return _expr

    def set_node(self, node: ast.Call):
        self.node = node

    def get_node(self):
        return self.node

    def set_var_access(self, var_access):
        self.var_access = var_access

    def get_var_access(self):
        return self.var_access

    def set_expr(self, expr):
        self.expr = expr

    def get_expr(self):
        return self.expr

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def add_args(self, arg):
        self.args.append(arg)
