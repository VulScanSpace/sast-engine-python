from model import AstModel


class VarDef(AstModel):
    expr = None
    name = None
    label = None
    value = None

    def __init__(self, ast_node):
        super().__init__(ast_node)

    def __str__(self) -> str:
        return self.expr

    def set_name(self, name):
        self.name = name

    def set_label(self, label):
        self.label = label

    def set_expr(self, expr):
        self.expr = expr

    def set_value(self, value):
        self.value = value
