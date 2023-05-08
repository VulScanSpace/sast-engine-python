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
