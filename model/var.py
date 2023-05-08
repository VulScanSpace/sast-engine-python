from model import AstModel


class VarDef(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.expr = ''
        self.name = ''
        self.label = None
        self.value = None
        self.annotation = list()
        self.type_comment = None
        self.instance = False
        self.default_value = None
        self.values = list()

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
