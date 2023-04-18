import ast


class AstModel(object):
    start_line = int()
    end_line = int()
    start_col = int()
    end_col = int()
    ast_node = None

    def __init__(self, ast_node):
        self.start_line = ast_node.lineno
        self.end_line = ast_node.end_lineno
        self.start_col = ast_node.col_offset
        self.end_col = ast_node.end_col_offset
        self.ast_node = ast_node
