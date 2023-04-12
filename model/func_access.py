import ast

from model import AstModel
from model.func import FuncDef


class FuncAccess(AstModel):
    expr = str()
    var_access = str()
    label = str()
    args = list()
    parent = FuncDef()
    node = None

    def __init__(self, start_line=-1, end_line=-1, start_col=-1, end_col=-1):
        super().__init__(start_line, end_line, start_col, end_col)

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
