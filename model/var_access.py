from model import AstModel


class VarAccess(AstModel):
    expr = str()
    var = str()
    label = str()

    def __init__(self, start_line=-1, end_line=-1, start_col=-1, end_col=-1):
        super().__init__(start_line, end_line, start_col, end_col)

    def set_var(self, var):
        self.var = var

    def get_var(self):
        return self.var

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def set_expr(self, expr):
        self.expr = expr

    def get_expr(self):
        return self.expr
