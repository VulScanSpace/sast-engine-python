from model import AstModel


class LiteralAccess(AstModel):
    expr = str()
    l_value = None
    l_type = None

    def __init__(self, start_line, end_line, start_col, end_col):
        super().__init__(start_line, end_line, start_col, end_col)

    def set_expr(self, expr):
        self.expr = expr

    def get_expr(self):
        return self.expr

    def set_value(self, _value):
        self.l_value = _value

    def get_value(self):
        return self.l_value

    def set_type(self, _type):
        self.l_type = _type

    def get_type(self):
        return self.l_type

    def __repr__(self) -> str:
        return str(self.expr)
