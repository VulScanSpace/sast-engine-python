from model import AstModel


class FuncDef(AstModel):
    name = str()
    annotations = list()
    args = list()
    rets = list()
    body_array = list()

    def __init__(self, start_line=-1, end_line=-1, start_col=-1, end_col=-1):
        super().__init__(start_line, end_line, start_col, end_col)

    def add_annotation(self, annotation):
        self.annotations.append(annotation)

    def add_args(self, arg):
        self.args.append(arg)

    def add_ret(self, ret):
        self.rets.append(ret)

    def add_body(self, body):
        self.body_array.append(body)
