from model import AstModel
from model.func import SFuncDef
from model.func_access import FuncAccess
from model.var import VarDef


class SClassDef(AstModel):
    def __init__(self, ast_node):
        super().__init__(ast_node)
        self.package = ''
        self.name = ''
        self.bases = list()
        self.class_field = list()
        self.static_field = list()
        self.func_def = list()
        self.var_def = list()
        self.class_func_access = dict()

    def add_base(self, base):
        self.bases.append(base)

    def add_var(self, var: VarDef):
        self.var_def.append(var)

    def add_func(self, func: SFuncDef):
        self.func_def.append(func)

    def set_name(self, name: str):
        self.name = name

    def get_name(self):
        return self.name

    def add_class_field(self, class_field):
        self.class_field.append(class_field)

    def add_func_access(self, func_access: FuncAccess):
        self.class_func_access[func_access.get_expr()] = func_access
