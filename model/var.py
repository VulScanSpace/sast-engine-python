from model import AstModel


class VarDef(AstModel):
    expr = str()
    name = str()
    label = str()

    def __init__(self, start_line=-1, end_line=-1, start_col=-1, end_col=-1):
        super().__init__(start_line, end_line, start_col, end_col)

    def set_name(self, name):
        self.name = name

    def set_label(self, label):
        self.label = label

    def set_expr(self, expr):
        self.expr = expr
