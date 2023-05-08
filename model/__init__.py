import ast


class AstModel(object):
    def __init__(self, ast_node):
        self.start_line = ast_node.lineno
        self.end_line = ast_node.end_lineno
        self.start_col = ast_node.col_offset
        self.end_col = ast_node.end_col_offset
        self.ast_node = ast_node
        self.parent = None

    def set_parent(self, parent):
        self.parent = parent


class ForModel(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.local_vars = list()
        self.var_value = None
        self.body = list()
        self.func_accesses = list()


class AstTuple(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.value = None

    def set_value(self, value):
        self.value = value

    def __str__(self) -> str:
        expr = '('
        for _value in self.value:
            expr = f'{expr}{_value}, '
        expr = f'({expr[:-2]})'
        return expr


class AstStr(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.values = list()

    def add_value(self, value):
        self.values.append(value)


class AstTry(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.body = list()
        self.except_body = list()
        self.else_body = list()
        self.final_body = list()

    def add_body(self, body):
        self.body.append(body)

    def add_except_body(self, body):
        self.except_body.append(body)

    def add_else_body(self, body):
        self.else_body.append(body)

    def add_final_body(self, body):
        self.final_body.append(body)


class AstWith(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.var_def = list()
        self.body = list()

    def add_var_def(self, var_def):
        self.var_def.append(var_def)

    def add_body(self, body):
        self.body.append(body)
