import ast

from model import AstModel


class SFuncDef(AstModel):
    name = str()
    annotations = list()
    args = list()
    rets = list()
    body_array = list()

    def __init__(self, ast_node):
        super().__init__(ast_node)

    def set_name(self, name: str):
        self.name = name

    def get_name(self):
        return self.name

    def add_annotation(self, annotation):
        self.annotations.append(annotation)

    def add_args(self, arg):
        self.args.append(arg)

    def add_ret(self, ret):
        self.rets.append(ret)

    def add_body(self, body):
        self.body_array.append(body)
