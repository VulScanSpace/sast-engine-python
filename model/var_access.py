from model import AstModel
from model.literal_access import LiteralAccess


class VarAccess(AstModel):
    expr = str()
    var = str()
    label = str()

    def __init__(self, ast_node):
        super().__init__(ast_node)

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
