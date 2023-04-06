import ast
import tokenize
from _ast import withitem, alias, keyword, arg, arguments, ExceptHandler, comprehension, NotIn, NotEq, LtE, Lt, IsNot, \
    Is, In, GtE, Gt, Eq, USub, UAdd, Not, Invert, Sub, RShift, Pow, MatMult, Mult, Mod, LShift, FloorDiv, Div, BitXor, \
    BitOr, BitAnd, Add, Or, And, Store, Load, Del, Tuple, List, Name, Starred, Subscript, Attribute, NamedExpr, \
    Constant, JoinedStr, FormattedValue, Call, Compare, YieldFrom, Yield, Await, GeneratorExp, DictComp, SetComp, \
    ListComp, Set, Dict, IfExp, Lambda, UnaryOp, BinOp, BoolOp, Slice, Continue, Break, Pass, Expr, Nonlocal, Global, \
    ImportFrom, Import, Assert, Try, Raise, AsyncWith, With, If, While, AsyncFor, For, AnnAssign, AugAssign, Assign, \
    Delete, Return, ClassDef, AsyncFunctionDef, FunctionDef, Expression, Interactive, Module, AST
from ast import NameConstant, Bytes, Str, Num, Param, AugStore, AugLoad, Suite, Index, ExtSlice
from typing import Any

import model
from model.Module import SModule
from model.s_field import SField


class SecurityNodeVisitor2(ast.NodeVisitor):
    def __init__(self):
        self.s_module = SModule()

    def str_node(self, node):
        if isinstance(node, ast.AST):
            fields = [(name, self.str_node(val)) for name, val in ast.iter_fields(node) if
                      name not in ('left', 'right')]
            rv = '%s(%s' % (node.__class__.__name__, ', '.join('%s=%s' % field for field in fields))
            return rv + ')'
        else:
            return repr(node)

    def visit_wrapper(self, node: AST):
        name = node.__class__.__name__
        method = "visit_" + name
        visitor = getattr(self, method, None)
        if visitor:
            return visitor(node)
        else:
            self.visit(node)

    def visit(self, node: AST) -> Any:
        print(self.str_node(node))
        for field, value in ast.iter_fields(node):
            items = value if isinstance(value, list) else list(value)

            for item in items:
                if isinstance(item, ast.AST):
                    self.visit_wrapper(item)

    def visit_Module(self, node) -> Any:
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)

    def visit_Interactive(self, node: Interactive) -> Any:
        return super().visit_Interactive(node)

    def visit_Expression(self, node: Expression) -> Any:
        return super().visit_Expression(node)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.s_module.funcs[''] = node
        func_name = node.name
        self.s_module.funcs[func_name] = node

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Any:
        return super().visit_AsyncFunctionDef(node)

    def visit_ClassDef(self, node: ClassDef) -> Any:
        return super().visit_ClassDef(node)

    def visit_Return(self, node: Return) -> Any:
        return super().visit_Return(node)

    def visit_Delete(self, node: Delete) -> Any:
        return super().visit_Delete(node)

    def visit_field(self, field, value):
        s_field = SField()
        s_field.name = field.id
        s_field_value = self.visit_wrapper(value)
        s_field.expr = f'{field.id} = {s_field_value}'
        s_field.value_pattern[s_field.expr] = model.s_field.SValuePattern()
        s_field.value_pattern[s_field.expr].value = s_field_value
        s_field.value_pattern[s_field.expr].type = value.__class__.__name__
        return s_field

    def visit_Assign(self, node: Assign) -> Any:
        """
        分配变量
        :param node:
        :return:
        """
        s_fields = list()
        targets = node.targets
        values = node.value
        type_comment = node.type_comment
        for field in targets:
            _field_ctx = field.ctx
            _field_value_ctx = values.ctx if hasattr(values, 'ctx') else None
            _fields = field.elts if isinstance(field, ast.Tuple) else field
            _field_values = values.elts if isinstance(values, ast.Tuple) else values

            if isinstance(_fields, list) and isinstance(_field_values, list):
                if len(_fields) == len(_field_values):
                    for _field, _field_value in zip(_fields, _field_values):
                        s_field = self.visit_field(_field, _field_value)
                        s_fields.append(s_field)
                else:
                    pass
            else:
                s_field = self.visit_field(_fields, _field_values)
                s_fields.append(s_field)
        return s_fields

    def visit_AugAssign(self, node: AugAssign) -> Any:
        return super().visit_AugAssign(node)

    def visit_AnnAssign(self, node: AnnAssign) -> Any:
        return super().visit_AnnAssign(node)

    def visit_For(self, node: For) -> Any:
        return super().visit_For(node)

    def visit_AsyncFor(self, node: AsyncFor) -> Any:
        return super().visit_AsyncFor(node)

    def visit_While(self, node: While) -> Any:
        return super().visit_While(node)

    def visit_If(self, node: If) -> Any:
        pass
        # return super().visit_If(node)

    def visit_With(self, node: With) -> Any:
        return super().visit_With(node)

    def visit_AsyncWith(self, node: AsyncWith) -> Any:
        return super().visit_AsyncWith(node)

    def visit_Raise(self, node: Raise) -> Any:
        return super().visit_Raise(node)

    def visit_Try(self, node: Try) -> Any:
        return super().visit_Try(node)

    def visit_Assert(self, node: Assert) -> Any:
        return super().visit_Assert(node)

    def visit_Import(self, node: Import) -> Any:
        for _module in node.names:
            module_name = _module.name
            alias_name = _module.asname if _module.asname else module_name
            self.s_module.imports[alias_name] = module_name

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        base_module_name = node.module
        for _module in node.names:
            module_name = f'{base_module_name}.{_module.name}' if base_module_name else _module.name
            alias_name = _module.asname if _module.asname else _module.name
            self.s_module.imports[alias_name] = module_name

    def visit_Global(self, node: Global) -> Any:
        return super().visit_Global(node)

    def visit_Nonlocal(self, node: Nonlocal) -> Any:
        return super().visit_Nonlocal(node)

    # FIXME 表达式解析，暂时注释，后续统一处理时打开
    def visit_Expr(self, node: Expr) -> Any:
        """
        expr = BoolOp(boolop op, expr* values)
         | NamedExpr(expr target, expr value)
         | BinOp(expr left, operator op, expr right)
         | UnaryOp(unaryop op, expr operand)
         | Lambda(arguments args, expr body)
         | IfExp(expr test, expr body, expr orelse)
         | Dict(expr* keys, expr* values)
         | Set(expr* elts)
         | ListComp(expr elt, comprehension* generators)
         | SetComp(expr elt, comprehension* generators)
         | DictComp(expr key, expr value, comprehension* generators)
         | GeneratorExp(expr elt, comprehension* generators)
         -- the grammar constrains where yield expressions can occur
         | Await(expr value)
         | Yield(expr? value)
         | YieldFrom(expr value)
         -- need sequences for compare to distinguish between
         -- x < 4 < 3 and (x < 4) < 3
         | Compare(expr left, cmpop* ops, expr* comparators)
         | Call(expr func, expr* args, keyword* keywords)
         | FormattedValue(expr value, int conversion, expr? format_spec)
         | JoinedStr(expr* values)
         | Constant(constant value, string? kind)

         -- the following expression can appear in assignment context
         | Attribute(expr value, identifier attr, expr_context ctx)
         | Subscript(expr value, expr slice, expr_context ctx)
         | Starred(expr value, expr_context ctx)
         | Name(identifier id, expr_context ctx)
         | List(expr* elts, expr_context ctx)
         | Tuple(expr* elts, expr_context ctx)

         -- can appear only in Subscript
         | Slice(expr? lower, expr? upper, expr? step)

          -- col_offset is the byte offset in the utf8 string the parser uses
          attributes (int lineno, int col_offset, int? end_lineno, int? end_col_offset)
        :param node:
        :return:
        """
        # 后续增加表达式相关的内容
        return self.visit_wrapper(node.value)

    def visit_Pass(self, node: Pass) -> Any:
        return super().visit_Pass(node)

    def visit_Break(self, node: Break) -> Any:
        return super().visit_Break(node)

    def visit_Continue(self, node: Continue) -> Any:
        return super().visit_Continue(node)

    def visit_Slice(self, node: Slice) -> Any:
        return super().visit_Slice(node)

    def visit_BoolOp(self, node: BoolOp) -> Any:
        return super().visit_BoolOp(node)

    def visit_BinOp(self, node: BinOp) -> Any:
        return super().visit_BinOp(node)

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        return super().visit_UnaryOp(node)

    def visit_Lambda(self, node: Lambda) -> Any:
        return super().visit_Lambda(node)

    def visit_IfExp(self, node: IfExp) -> Any:
        return super().visit_IfExp(node)

    def visit_Dict(self, node: Dict) -> Any:
        return super().visit_Dict(node)

    def visit_Set(self, node: Set) -> Any:
        return super().visit_Set(node)

    def visit_ListComp(self, node: ListComp) -> Any:
        return super().visit_ListComp(node)

    def visit_SetComp(self, node: SetComp) -> Any:
        return super().visit_SetComp(node)

    def visit_DictComp(self, node: DictComp) -> Any:
        return super().visit_DictComp(node)

    def visit_GeneratorExp(self, node: GeneratorExp) -> Any:
        return super().visit_GeneratorExp(node)

    def visit_Await(self, node: Await) -> Any:
        return super().visit_Await(node)

    def visit_Yield(self, node: Yield) -> Any:
        return super().visit_Yield(node)

    def visit_YieldFrom(self, node: YieldFrom) -> Any:
        return super().visit_YieldFrom(node)

    def visit_Compare(self, node: Compare) -> Any:
        return super().visit_Compare(node)

    def visit_Call(self, node: Call) -> Any:
        expr = ""
        func = node.func
        func_name = ""
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = f'{func.value.id}.{func.attr}'
        else:
            pass

        self.s_module.func_access[func_name] = node
        expr = f'{func_name}({"args"})'
        return expr

    def visit_FormattedValue(self, node: FormattedValue) -> Any:
        return super().visit_FormattedValue(node)

    def visit_JoinedStr(self, node: JoinedStr) -> Any:
        return super().visit_JoinedStr(node)

    def visit_Constant(self, node: Constant) -> Any:
        return node.value

    def visit_NamedExpr(self, node: NamedExpr) -> Any:
        return super().visit_NamedExpr(node)

    def visit_Attribute(self, node: Attribute) -> Any:
        return super().visit_Attribute(node)

    def visit_Subscript(self, node: Subscript) -> Any:
        return super().visit_Subscript(node)

    def visit_Starred(self, node: Starred) -> Any:
        return super().visit_Starred(node)

    def visit_Name(self, node: Name) -> Any:
        return super().visit_Name(node)

    def visit_List(self, node: List) -> Any:
        return super().visit_List(node)

    def visit_Tuple(self, node: Tuple) -> Any:
        return super().visit_Tuple(node)

    def visit_Del(self, node: Del) -> Any:
        return super().visit_Del(node)

    def visit_Load(self, node: Load) -> Any:
        return super().visit_Load(node)

    def visit_Store(self, node: Store) -> Any:
        return super().visit_Store(node)

    def visit_And(self, node: And) -> Any:
        return super().visit_And(node)

    def visit_Or(self, node: Or) -> Any:
        return super().visit_Or(node)

    def visit_Add(self, node: Add) -> Any:
        return super().visit_Add(node)

    def visit_BitAnd(self, node: BitAnd) -> Any:
        return super().visit_BitAnd(node)

    def visit_BitOr(self, node: BitOr) -> Any:
        return super().visit_BitOr(node)

    def visit_BitXor(self, node: BitXor) -> Any:
        return super().visit_BitXor(node)

    def visit_Div(self, node: Div) -> Any:
        return super().visit_Div(node)

    def visit_FloorDiv(self, node: FloorDiv) -> Any:
        return super().visit_FloorDiv(node)

    def visit_LShift(self, node: LShift) -> Any:
        return super().visit_LShift(node)

    def visit_Mod(self, node: Mod) -> Any:
        return super().visit_Mod(node)

    def visit_Mult(self, node: Mult) -> Any:
        return super().visit_Mult(node)

    def visit_MatMult(self, node: MatMult) -> Any:
        return super().visit_MatMult(node)

    def visit_Pow(self, node: Pow) -> Any:
        return super().visit_Pow(node)

    def visit_RShift(self, node: RShift) -> Any:
        return super().visit_RShift(node)

    def visit_Sub(self, node: Sub) -> Any:
        return super().visit_Sub(node)

    def visit_Invert(self, node: Invert) -> Any:
        return super().visit_Invert(node)

    def visit_Not(self, node: Not) -> Any:
        return super().visit_Not(node)

    def visit_UAdd(self, node: UAdd) -> Any:
        return super().visit_UAdd(node)

    def visit_USub(self, node: USub) -> Any:
        return super().visit_USub(node)

    def visit_Eq(self, node: Eq) -> Any:
        return super().visit_Eq(node)

    def visit_Gt(self, node: Gt) -> Any:
        return super().visit_Gt(node)

    def visit_GtE(self, node: GtE) -> Any:
        return super().visit_GtE(node)

    def visit_In(self, node: In) -> Any:
        return super().visit_In(node)

    def visit_Is(self, node: Is) -> Any:
        return super().visit_Is(node)

    def visit_IsNot(self, node: IsNot) -> Any:
        return super().visit_IsNot(node)

    def visit_Lt(self, node: Lt) -> Any:
        return super().visit_Lt(node)

    def visit_LtE(self, node: LtE) -> Any:
        return super().visit_LtE(node)

    def visit_NotEq(self, node: NotEq) -> Any:
        return super().visit_NotEq(node)

    def visit_NotIn(self, node: NotIn) -> Any:
        return super().visit_NotIn(node)

    def visit_comprehension(self, node: comprehension) -> Any:
        return super().visit_comprehension(node)

    def visit_ExceptHandler(self, node: ExceptHandler) -> Any:
        return super().visit_ExceptHandler(node)

    def visit_arguments(self, node: arguments) -> Any:
        return super().visit_arguments(node)

    def visit_arg(self, node: arg) -> Any:
        return super().visit_arg(node)

    def visit_keyword(self, node: keyword) -> Any:
        return super().visit_keyword(node)

    def visit_alias(self, node: alias) -> Any:
        return super().visit_alias(node)

    def visit_withitem(self, node: withitem) -> Any:
        return super().visit_withitem(node)

    def visit_ExtSlice(self, node: ExtSlice) -> Any:
        return super().visit_ExtSlice(node)

    def visit_Index(self, node: Index) -> Any:
        return super().visit_Index(node)

    def visit_Suite(self, node: Suite) -> Any:
        return super().visit_Suite(node)

    def visit_AugLoad(self, node: AugLoad) -> Any:
        return super().visit_AugLoad(node)

    def visit_AugStore(self, node: AugStore) -> Any:
        return super().visit_AugStore(node)

    def visit_Param(self, node: Param) -> Any:
        return super().visit_Param(node)

    def visit_Num(self, node: Num) -> Any:
        return super().visit_Num(node)

    def visit_Str(self, node: Str) -> Any:
        print(f'lit: {node.value}')

    def visit_Bytes(self, node: Bytes) -> Any:
        return super().visit_Bytes(node)

    def visit_NameConstant(self, node: NameConstant) -> Any:
        return super().visit_NameConstant(node)

    def visit_Ellipsis(self, node: Ellipsis) -> Any:
        return super().visit_Ellipsis(node)


class SecurityNodeVisitor:
    def visit_module(self, source_code):
        s_module = ast.parse(source_code)
        nv = SecurityNodeVisitor2()
        nv.visit(s_module)
        print(nv.s_module)
        return "None"

    def _visit_import(self, node):
        """
        # 层级、完整包名、别名
        :param node:
        :return:
        """
        col_offset, end_col_offset, lineno, end_lineno = node.col_offset, node.end_col_offset, node.lineno, node.end_lineno

        def show_meta(module_name, alias_name):
            print(f'module: {alias_name} is {module_name}:{col_offset}:{end_col_offset}:{lineno}:{end_lineno}')

        if isinstance(node, ast.Import):
            for _module in node.names:
                module_name = _module.name
                alias_name = _module.asname if _module.asname else module_name
                show_meta(module_name, alias_name)
        elif isinstance(node, ast.ImportFrom):
            base_module_name = node.module
            for _module in node.names:
                module_name = f'{base_module_name}.{_module.name}' if base_module_name else _module.name
                alias_name = _module.asname if _module.asname else _module.name
                show_meta(module_name, alias_name)

    def _visit_class_def(self, node):
        pass

    def _visit_function_def(self, node):
        # 方法名
        # 参数
        # 方法体
        # 返回值
        pass


if __name__ == "__main__":
    filename = '/Users/owefsad/PycharmProjects/bandit/bandit/cli/main.py'
    s = SecurityNodeVisitor()
    with open(filename) as f:
        fdata = f.read()
        module_meta = s.visit_module(fdata)
        print(module_meta)
