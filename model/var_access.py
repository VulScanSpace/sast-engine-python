import ast

from model import AstModel


class VarAccess(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.var = None
        self.label = None
        self.expr = None
        self.values = dict()

    def __str__(self) -> str:
        if isinstance(self.ast_node, ast.Subscript):
            return f'{self.var}[{self.label}]'
        elif isinstance(self.ast_node, ast.Starred):
            return f'*{self.var}'
        else:
            return f'{self.var}.{self.label}' if self.label else self.var

    def set_var(self, var):
        self.var = var

    def get_var(self):
        return self.var

    def set_label(self, label):
        self.label = label

    def add_label(self, label):
        print()

    def get_label(self):
        return self.label

    def set_expr(self, expr):
        self.expr = expr

    def get_expr(self):
        return self.expr

    def set_args(self):
        self.args = True

    def add_value(self, value):
        self.values[str(value)] = value
