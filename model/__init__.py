class AstModel(object):
    start_line = int()
    end_line = int()
    start_col = int()
    end_col = int()

    def __init__(self, start_line, end_line, start_col, end_col):
        self.start_line = start_line
        self.end_line = end_line
        self.start_col = start_col
        self.end_col = end_col
