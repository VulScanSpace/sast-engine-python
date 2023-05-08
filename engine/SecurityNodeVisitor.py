import ast
from _ast import withitem, alias, keyword, arg, arguments, ExceptHandler, comprehension, NotIn, NotEq, LtE, Lt, IsNot, \
    Is, In, GtE, Gt, Eq, USub, UAdd, Not, Invert, Sub, RShift, Pow, MatMult, Mult, Mod, LShift, FloorDiv, Div, BitXor, \
    BitOr, BitAnd, Add, Or, And, Store, Load, Del, Tuple, List, Name, Starred, Subscript, Attribute, NamedExpr, \
    Constant, JoinedStr, FormattedValue, Call, Compare, YieldFrom, Yield, Await, GeneratorExp, DictComp, SetComp, \
    ListComp, Set, Dict, IfExp, Lambda, UnaryOp, BinOp, BoolOp, Slice, Continue, Break, Pass, Expr, Nonlocal, Global, \
    Assert, Try, Raise, AsyncWith, With, If, While, AsyncFor, For, AnnAssign, AugAssign, Assign, \
    Delete, Return, ClassDef, AsyncFunctionDef, FunctionDef, Expression, Interactive, AST
from ast import NameConstant, Bytes, Str, Num, Param, AugStore, AugLoad, Suite, Index, ExtSlice
from typing import Any

import model
from model.Module import SModule
from model.class_def import SClassDef
from model.func import SFuncDef
from model.func_access import FuncAccess
from model.import_access import ImportAccess
from model.literal_access import LiteralAccess
from model.s_field import SField
from model.var import VarDef
from model.var_access import VarAccess


class SecurityNodeVisitor(ast.NodeVisitor):
    def __init__(self, filename, _ast):
        self.s_module = SModule(filename)
        self.visit_Module(_ast)

    @staticmethod
    def is_import(node):
        return isinstance(node, (ast.Import, ast.ImportFrom))

    def get_module(self):
        return self.s_module

    def str_node(self, node):
        if isinstance(node, ast.AST):
            fields = [(name, self.str_node(val)) for name, val in ast.iter_fields(node) if
                      name not in ('left', 'right')]
            rv = '%s(%s' % (node.__class__.__name__, ', '.join('%s=%s' % field for field in fields))
            return rv + ')'
        else:
            return repr(node)

    def visit_wrapper(self, node):
        name = node.__class__.__name__
        if self.is_import(node):
            return self.visit_Import(node)
        method = "visit_" + name
        visitor = getattr(self, method, None)
        if visitor:
            return visitor(node)
        else:
            self.visit(node)

    def visit(self, node: AST) -> Any:
        print(self.str_node(node))
        for body in node.body:
            if isinstance(body, (ast.Import, ast.ImportFrom)):
                packages = self.visit_Import(body)
                for package in packages:
                    self.s_module.imports[package.alias] = packages
            elif isinstance(body, ast.Assign):
                fields = self.visit_Assign(body)
                # FIXME field 存在多次 assign，以最后一次的值为准
                for field in fields:
                    self.s_module.global_fields[field.name.expr] = field
            elif isinstance(body, ast.ClassDef):
                class_def = self.visit_ClassDef(body)
                self.s_module.global_class_def.append(class_def)
            elif isinstance(body, ast.FunctionDef):
                func_def = self.visit_FunctionDef(body)
                self.s_module.funcs.append(func_def)
            else:
                print(self.s_module.filename)
                print(type(body))
                print()

    def visit_Module(self, node) -> Any:
        for item in node.body:
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                packages = self.visit_Import(item)
                for package in packages:
                    self.s_module.imports[package.alias] = packages
            elif isinstance(item, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                fields = list()
                if isinstance(item, ast.Assign):
                    fields = self.visit_Assign(item)
                elif isinstance(item, ast.AugAssign):
                    fields = self.visit_AugAssign(item)
                elif isinstance(item, ast.AnnAssign):
                    fields = self.visit_AnnAssign(item)

                # FIXME field 存在多次 assign，以最后一次的值为准
                for field in fields:
                    # 如果存在，则复制，如果不存在，则保存
                    self.s_module.global_fields[field.name.expr] = field
            elif isinstance(item, ast.ClassDef):
                class_def = self.visit_ClassDef(item)
                self.s_module.global_class_def.append(class_def)
            elif isinstance(item, ast.FunctionDef):
                func_def = self.visit_FunctionDef(item)
                self.s_module.funcs.append(func_def)
            else:
                print(self.s_module.filename)
                print(type(item))
                print()

    def visit_Interactive(self, node: Interactive) -> Any:
        return super().visit_Interactive(node)

    def visit_Expression(self, node: Expression) -> Any:
        return super().visit_Expression(node)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        func = SFuncDef(node)
        func.set_name(node.name)

        for item in node.decorator_list:
            func.add_annotation(self.visit_wrapper(item))

        func.set_args(self.visit_arguments(node.args))

        for item in node.body:
            if isinstance(item, ast.AsyncFunctionDef):
                print()
            elif isinstance(item, ast.FunctionDef):
                print()
            elif isinstance(item, ast.ClassDef):
                _class_def = self.visit_ClassDef(item)
                func.add_body(_class_def)
            elif isinstance(item, ast.Return):
                _ = self.visit_Return(item)
                func.rets.append(_)
            elif isinstance(item, ast.Delete):
                _ = self.visit_Delete(item)
                func.add_body(_)
            elif isinstance(item, ast.Assign):
                var_defs = self.visit_Assign(item)
                for _var_def in var_defs:
                    func.add_local_var(_var_def)
                    func.add_body(_var_def)
            elif isinstance(item, ast.AugAssign):
                var_defs = self.visit_AugAssign(item)
                for _var_def in var_defs:
                    func.add_local_var(_var_def)
                    func.add_body(_var_def)
            elif isinstance(item, ast.AnnAssign):
                print()
            elif isinstance(item, ast.For):
                _ = self.visit_For(item)
                func.add_body(_)
            elif isinstance(item, ast.AsyncFor):
                print()
            elif isinstance(item, ast.While):
                print()
            elif isinstance(item, ast.If):
                print()
            elif isinstance(item, ast.With):
                _with = self.visit_With(item)
                _with.set_parent(func)
                func.add_body(_with)
            elif isinstance(item, ast.AsyncWith):
                print()
            # elif isinstance(item, ast.Match):
            #     print()
            elif isinstance(item, ast.Raise):
                print()
            elif isinstance(item, ast.Try):
                try_expr = self.visit_Try(item)
                try_expr.set_parent(func)
                func.add_body(try_expr)
            elif isinstance(item, ast.Assert):
                print()
            elif isinstance(item, ast.Import):
                print()
            elif isinstance(item, ast.ImportFrom):
                print()
            elif isinstance(item, ast.Global):
                print()
            elif isinstance(item, ast.Nonlocal):
                print()
            elif isinstance(item, ast.Expr):
                _expr_value = item.value
                if isinstance(_expr_value, ast.BoolOp):
                    self.visit_BoolOp(_expr_value)
                elif isinstance(_expr_value, ast.NamedExpr):
                    print()
                elif isinstance(_expr_value, ast.BinOp):
                    print()
                elif isinstance(_expr_value, ast.UnaryOp):
                    print()
                elif isinstance(_expr_value, ast.Lambda):
                    print()
                elif isinstance(_expr_value, ast.IfExp):
                    print()
                elif isinstance(_expr_value, ast.Dict):
                    print()
                elif isinstance(_expr_value, ast.Set):
                    print()
                elif isinstance(_expr_value, ast.ListComp):
                    print()
                elif isinstance(_expr_value, ast.SetComp):
                    print()
                elif isinstance(_expr_value, ast.DictComp):
                    print()
                elif isinstance(_expr_value, ast.GeneratorExp):
                    print()
                elif isinstance(_expr_value, ast.Await):
                    print()
                elif isinstance(_expr_value, ast.Yield):
                    print()
                elif isinstance(_expr_value, ast.YieldFrom):
                    print()
                elif isinstance(_expr_value, ast.Compare):
                    print()
                elif isinstance(_expr_value, ast.Call):
                    func_access = self.visit_Call(_expr_value)
                    func_access.set_parent(func)
                    func.add_body(func_access)
                elif isinstance(_expr_value, ast.FormattedValue):
                    print()
                elif isinstance(_expr_value, ast.JoinedStr):
                    print()
                elif isinstance(_expr_value, ast.Constant):
                    continue
                elif isinstance(_expr_value, ast.Attribute):
                    print()
                elif isinstance(_expr_value, ast.Subscript):
                    print()
                elif isinstance(_expr_value, ast.Starred):
                    print()
                elif isinstance(_expr_value, ast.Name):
                    print()
                elif isinstance(_expr_value, ast.List):
                    print()
                elif isinstance(_expr_value, ast.Tuple):
                    print()
                elif isinstance(_expr_value, ast.Slice):
                    print()
                else:
                    print()
            else:
                continue

        if node.returns is not None:
            print()

        return func

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Any:
        return super().visit_AsyncFunctionDef(node)

    def visit_ClassDef(self, node: ClassDef) -> Any:
        class_def = SClassDef(node)
        class_def.set_name(node.name)
        for item in node.bases:
            base_class = self.visit_wrapper(item)
            class_def.add_base(base_class)

        keywords = [self.visit_wrapper(item) for item in node.keywords]
        for item in node.body:
            if isinstance(item, ast.Assign):
                var_def = self.visit_Assign(item)
                class_def.add_class_field(var_def)
            elif isinstance(item, ast.FunctionDef):
                func_def = self.visit_FunctionDef(item)
                class_def.add_func(func_def)
            elif isinstance(item, ast.Expr):
                if isinstance(item.value, ast.Constant):
                    continue
                elif isinstance(item.value, ast.Call):
                    class_def.add_func_access(self.visit_Call(item.value))
                else:
                    self.visit_wrapper(item.value)
        return class_def

    def visit_Return(self, node: Return) -> Any:
        if node.value is None:
            return 'return'
        value = self.visit_wrapper(node.value)
        return f'return {value}'

    def visit_Delete(self, node: Delete) -> Any:
        _targets = [str(self.visit_wrapper(_)) for _ in node.targets]
        _expr = f'delete {", ".join(_targets)}'
        print(_expr)
        return _expr

    def visit_field(self, field, value):
        s_field = SField()
        s_field.name = self.visit_wrapper(field)
        if isinstance(value, list):
            s_field_value = [self.visit_wrapper(item) for item in value]
            s_field.expr = f'{s_field.name} = {s_field_value}'
            s_field.value_pattern[s_field.expr] = model.s_field.SValuePattern()
            s_field.value_pattern[s_field.expr].value = s_field_value
            s_field.value_pattern[s_field.expr].type = value.__class__.__name__
            return s_field
        else:
            s_field_value = self.visit_wrapper(value)
            s_field.expr = f'{s_field.name.expr} = {s_field_value}'
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

        if len(targets) > 1:
            var_def = VarDef(node)
            _var_list = [self.visit_wrapper(_) for _ in targets]
            for _var_def in _var_list:
                if isinstance(values, ast.Tuple):
                    _var_values = self.visit_Tuple(values)
                    var_def.set_value(_var_values)
                    var_def.set_expr(f'{_var_def.expr} = ({", ".join([str(_) for _ in _var_values])})')
                elif isinstance(values, ast.List):
                    _var_values = self.visit_List(values)
                    var_def.set_value(_var_values)
                    var_def.set_expr(f'{_var_def.expr} = [{", ".join([str(_) for _ in _var_values])}]')
                else:
                    _var_values = self.visit_wrapper(values)
                    var_def.set_value(_var_values)
                    var_def.set_expr(f'{_var_def.expr} = {str(_var_values)}')
        else:
            _var = targets[0]
            if isinstance(_var, ast.Tuple):
                if isinstance(values, (ast.Tuple, ast.List)):
                    for _field, _field_value in zip(_var.elts, values.elts):
                        s_field = self.visit_field(_field, _field_value)
                        s_fields.append(s_field)
                else:
                    _var_names = self.visit_Tuple(_var)
                    _var_value = self.visit_wrapper(values)
                    index = 0
                    for _var in _var_names:
                        var_def = VarDef(node)
                        var_def.set_name(_var)
                        var_def.set_value(_var_value)
                        var_def.set_expr(f'{_var.expr} = {_var_value.expr}[{index}]')
                        index += 1
                        s_fields.append(var_def)
            else:
                var_def = VarDef(node)
                _var_def = self.visit_wrapper(_var)
                var_def.set_name(_var_def)
                if isinstance(values, ast.Tuple):
                    _var_values = self.visit_Tuple(values)
                    var_def.set_value(_var_values)
                    var_def.set_expr(f'{_var_def.expr} = ({", ".join([str(_) for _ in _var_values])})')
                elif isinstance(values, ast.List):
                    _var_values = self.visit_List(values)
                    var_def.set_value(_var_values)
                    var_def.set_expr(f'{_var_def.expr} = [{", ".join([str(_) for _ in _var_values])}]')
                else:
                    _var_values = self.visit_wrapper(values)
                    var_def.set_value(_var_values)
                    var_def.set_expr(f'{_var_def.expr} = {str(_var_values)}')
                s_fields.append(var_def)
        return s_fields

    def visit_AugAssign(self, node: AugAssign) -> Any:
        var_def = self.visit_Name(node.target)
        value = self.visit_Expr(node.value)
        var_def.add_value(value)
        var_def.set_value(value + var_def.get_value())
        return var_def

    def visit_AnnAssign(self, node: AnnAssign) -> Any:
        return super().visit_AnnAssign(node)

    def visit_For(self, node: For) -> Any:
        for_model = model.ForModel(node)

        _ = self.visit_Name(node.target)
        _var_def = VarDef(node.target)
        _var_def.set_name(_.get_var())
        _var_def.set_parent(for_model)

        for_model.local_vars.append(_var_def)

        # iter
        _var_accesses = self.visit_wrapper(node.iter)
        if isinstance(_var_accesses, list):
            for _var_access in _var_accesses:
                _var_access.set_parent(for_model)
        else:
            _var_accesses.set_parent(for_model)

        _var_def.set_value(_var_accesses)

        # body
        for item in node.body:
            if isinstance(item, ast.Assign):
                _local_vars = self.visit_Assign(item)
                for _ in _local_vars:
                    _.set_parent(for_model)
                    for_model.body.append(_)
            elif isinstance(item, ast.Call) or (isinstance(item, ast.Expr) and isinstance(item.value, ast.Call)):
                _func_access = self.visit_Call(item if isinstance(item, ast.Call) else item.value)
                _func_access.set_parent(for_model)
                for_model.body.append(_func_access)
                for_model.func_accesses.append(_func_access)
            else:
                _ = self.visit_wrapper(item)
                _.set_parent(for_model)
                for_model.body.append(_)

        for item in node.orelse:
            print()
            loop_else = [self.visit_wrapper(item) for item in node.orelse]
        return for_model

    def visit_AsyncFor(self, node: AsyncFor) -> Any:
        return super().visit_AsyncFor(node)

    def visit_While(self, node: While) -> Any:
        condition = self.visit_wrapper(node.test)
        body_items = [self.visit_wrapper(_) for _ in node.body]
        orelse = [self.visit_wrapper(_) for _ in node.orelse]
        return condition

    def visit_If(self, node: If) -> Any:
        test = node.test
        body = node.body
        orelse = node.orelse
        test_expr = self.visit_wrapper(test)
        expr = f'if {test_expr}:'
        for item in body:
            body_expr = self.visit_wrapper(item)
            if isinstance(body_expr, SField):
                expr = f'{expr}\n\t{body_expr.expr}'
            else:
                expr = f'{expr}\n\t{body_expr}'
        if orelse:
            else_values = [self.visit_wrapper(item) for item in orelse]
            orelse_exprs = ''
            for else_value in else_values:
                if isinstance(else_value, SField):
                    orelse_exprs = f'{orelse_exprs}\n\t{else_value.expr}'
                else:
                    orelse_exprs = f'{orelse_exprs}\n\t{else_value}'
            expr = f'{expr}\nelse:{orelse_exprs}'
        print(expr)
        return expr

    def visit_With(self, node: With) -> Any:
        """
        一个 with 代码块。 items 是一个代表上下文管理器的 withitem 节点列表，而 body 是该上下文中的缩进代码块。

        :param node:
        :return:
        """
        ast_with = model.AstWith(node)
        for item in node.items:
            _item = self.visit_withitem(item)
            ast_with.add_var_def(_item)

        for item in node.body:
            _body = self.visit_wrapper(item)
            ast_with.add_body(_body)
        with_item_expr = [self.visit_wrapper(item) for item in node.items]
        body_expr = [self.visit_wrapper(item) for item in node.body]
        expr = 'with'
        for item in with_item_expr:
            expr = f'{expr} {item},'
        expr = expr[:-1]
        expr = f'{expr}:'
        for item in body_expr:
            if isinstance(item, SField):
                expr = f'{expr}\n\t{item.expr}'
            else:
                expr = f'{expr}\n\t{item}'
        print(expr)
        return ast_with

    def visit_AsyncWith(self, node: AsyncWith) -> Any:
        return super().visit_AsyncWith(node)

    def visit_Raise(self, node: Raise) -> Any:
        _expr = 'raise'
        cause_expr = self.visit_wrapper(node.cause) if node.cause else None
        exc_expr = self.visit_wrapper(node.exc) if node.exc else None
        if cause_expr is not None:
            pass
        if exc_expr is not None:
            _expr = _expr + ' ' + str(exc_expr)

        return _expr

    def visit_Try(self, node: Try) -> Any:
        """
        try 代码块。 所有属性都是要执行的节点列表，除了 handlers，它是一个 ExceptHandler 节点列表。

        :param node:
        :return:
        """
        ast_try = model.AstTry(node)
        for item in node.body:
            body = self.visit_wrapper(item)
            ast_try.add_body(body)

        for item in node.handlers:
            body = self.visit_wrapper(item)
            ast_try.add_except_body(body)

        for item in node.orelse:
            body = self.visit_wrapper(item)
            ast_try.add_else_body(body)

        for item in node.finalbody:
            body = self.visit_wrapper(item)
            ast_try.add_final_body(body)

        body_expr = [self.visit_wrapper(item) for item in node.body]
        handler_expr = [self.visit_wrapper(item) for item in node.handlers]
        orelse_expr = [self.visit_wrapper(item) for item in node.orelse]
        finalbody_expr = [self.visit_wrapper(item) for item in node.finalbody]
        expr = 'try:'
        for item in body_expr:
            if isinstance(item, SField):
                expr = f'{expr}\n\t{item.expr}'
            else:
                expr = f'{expr}\n\t{item}'
        for item in handler_expr:
            expr = f'{expr}\n{item}'
        for item in orelse_expr:
            expr = f'{expr}\n{item}'
        for item in finalbody_expr:
            expr = f'{expr}\n{item}'
        print(expr)
        return ast_try

    def visit_Assert(self, node: Assert) -> Any:
        return super().visit_Assert(node)

    def visit_Import(self, node):
        packages = list()
        if isinstance(node, ast.Import):
            for _module in node.names:
                module_name = _module.name
                alias_name = _module.asname if _module.asname else module_name
                packages.append(ImportAccess(None, module_name, alias_name))
        else:
            base_module_name = node.module
            for _module in node.names:
                module_name = f'{base_module_name}.{_module.name}' if base_module_name else _module.name
                alias_name = _module.asname if _module.asname else _module.name
                packages.append(ImportAccess(None, module_name, alias_name))
        return packages

    def visit_Global(self, node: Global) -> Any:
        # 从全局变量中获取 var
        return [self.s_module.global_fields.get(_) for _ in node.names]

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
        return 'pass'

    def visit_Break(self, node: Break) -> Any:
        return 'break'

    def visit_Continue(self, node: Continue) -> Any:
        return 'continue'

    def visit_Slice(self, node: Slice) -> Any:
        _lower = None if node.lower is None else self.visit_wrapper(node.lower)
        _upper = None if node.upper is None else self.visit_wrapper(node.upper)
        _step = None if node.step is None else self.visit_wrapper(node.step)
        _expr = ''
        if _lower:
            _expr = f'{_lower}'
        _expr = f'{_expr}:'
        if _upper:
            _expr = f'{_expr}{_upper}'
        if _step:
            _expr = f'{_expr}:{_step}'
        return _expr

    def visit_BoolOp(self, node: BoolOp) -> Any:
        op_expr = self.visit_wrapper(node.op)
        value_exprs = [self.visit_wrapper(item) for item in node.values]
        expr = ''
        for value_expr in value_exprs:
            if isinstance(value_expr, list):
                expr = f'{expr} {op_expr} {str(value_expr)}'
            else:
                expr = f'{expr} {op_expr} {value_expr}'
        return expr[len(op_expr) + 2:]

    def visit_BinOp(self, node: BinOp) -> Any:
        """
        双目运算（如相加或相减）。 op 是运算符，而 left 和 right 是任意表达式节点。

        :param node:
        :return:
        """
        left_expr = self.visit_wrapper(node.left)
        op_expr = self.visit_wrapper(node.op)
        right_expr = self.visit_wrapper(node.right)
        expr = f'{left_expr} {op_expr} {str(right_expr)}'
        print(expr)
        return expr

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        op = self.visit_wrapper(node.op)
        operand = self.visit_wrapper(node.operand)
        return f'{op} {operand}'

    def visit_Lambda(self, node: Lambda) -> Any:
        arg_expr = self.visit_wrapper(node.args)
        body_expr = self.visit_wrapper(node.body)
        expr = f'lambda {arg_expr}: {body_expr}'
        return expr

    def visit_IfExp(self, node: IfExp) -> Any:
        """
        一个表达式例如 a if b else c。 每个字段保存一个单独节点，因而在下面的示例中，三个节点均为 Name 节点。

        print(ast.dump(ast.parse('a if b else c', mode='eval'), indent=4))
        Expression(
            body=IfExp(
                test=Name(id='b', ctx=Load()),
                body=Name(id='a', ctx=Load()),
                orelse=Name(id='c', ctx=Load())
            )
        )

        :param node:
        :return:
        """
        body_expr = self.visit_wrapper(node.body)
        test_expr = self.visit_wrapper(node.test)
        else_expr = self.visit_wrapper(node.orelse)
        return f'{body_expr} if {test_expr} else {else_expr}'

    def visit_Dict(self, node: Dict) -> Any:
        dict_expr = dict()
        for key, value in zip(node.keys, node.values):
            dict_expr[self.visit_wrapper(key)] = self.visit_wrapper(value)
        return dict_expr if dict_expr else '{}'

    def visit_Set(self, node: Set) -> Any:
        value = set()
        for elt in node.elts:
            value.add(self.visit_wrapper(elt))
        return value

    def visit_comp(self, node):
        if hasattr(node, 'elt'):
            _elt = self.visit_wrapper(node.elt)
            _expr = ''
            if isinstance(node.elt, ast.Tuple):
                _expr = f'({", ".join([str(_) for _ in _elt])})'
            else:
                _expr = f'({_elt})'
                pass
            for _generator in node.generators:
                _generator_value = self.visit_comprehension(_generator)
                _expr = f'{_expr} {_generator_value}'
            print(_expr)
        else:
            _key = self.visit_Name(node.key)
            _value = self.visit_wrapper(node.value)
            _expr = '{'
            _expr = f'{_expr}{_key}: {_value}'
            for _generator in node.generators:
                _generator_value = self.visit_comprehension(_generator)
                _expr = f'{_expr} {_generator_value}'
            _expr = _expr + '}'
            print(_expr)
        return _expr

    def visit_ListComp(self, node: ListComp) -> Any:
        body_expr = self.visit_wrapper(node.elt)
        generator_expr = [self.visit_wrapper(item) for item in node.generators]
        return f'[{body_expr} {" ".join(generator_expr)}]'

    def visit_SetComp(self, node: SetComp) -> Any:
        return self.visit_comp(node)

    def visit_DictComp(self, node: DictComp) -> Any:
        if hasattr(node, 'elt'):
            _elt = self.visit_wrapper(node.elt)
            _expr = ''
            if isinstance(node.elt, ast.Tuple):
                _expr = f'({", ".join([str(_) for _ in _elt])})'
            else:
                pass

            for _generator in node.generators:
                _generator_value = self.visit_comprehension(_generator)
                _expr = f'{_expr} {_generator_value}'
            print(_expr)
        else:
            _key = self.visit_wrapper(node.key)
            _value = self.visit_wrapper(node.value)
            _expr = '{'
            _expr = f'{_expr}{_key}: {_value}'
            for _generator in node.generators:
                _generator_value = self.visit_comprehension(_generator)
                _expr = f'{_expr} {_generator_value}'
            _expr = _expr + '}'
            print(_expr)
        return _expr

    def visit_GeneratorExp(self, node: GeneratorExp) -> Any:
        if hasattr(node, 'elt'):
            _elt = self.visit_wrapper(node.elt)
            _expr = ''
            if isinstance(node.elt, ast.Tuple):
                _expr = f'({", ".join([str(_) for _ in _elt])})'
            else:
                pass

            for _generator in node.generators:
                _generator_value = self.visit_comprehension(_generator)
                _expr = f'{_expr} {_generator_value}'
            print(_expr)
        else:
            print()
        return _expr

    def visit_Await(self, node: Await) -> Any:
        return super().visit_Await(node)

    def visit_Yield(self, node: Yield) -> Any:
        yield_value = self.visit_Name(node.value)
        return yield_value

    def visit_YieldFrom(self, node: YieldFrom) -> Any:
        yield_value = self.visit_Name(node.value)
        return yield_value

    def visit_Compare(self, node: Compare) -> Any:
        left = node.left
        ops = node.ops
        comparators = node.comparators
        left_expr = self.visit_wrapper(left)
        op_exprs = [self.visit_wrapper(op) for op in ops]
        comparator_expr = None
        if len(comparators) > 1:
            print(comparators)
        else:
            comparator_expr = self.visit_wrapper(comparators[0])

        full_expr = f'{left_expr.expr if isinstance(left_expr, VarAccess) else left_expr} {" ".join(op_exprs)} {comparator_expr.expr if isinstance(comparator_expr, LiteralAccess) else str(comparator_expr)}'
        self.s_module.expr[full_expr] = node
        return full_expr

    def visit_Call(self, node: Call) -> Any:
        func_access = FuncAccess(node)
        func_access.set_node(node)

        func = node.func

        if isinstance(func, ast.Name):
            func_access.name = func.id
            func_access.expr = func.id
        elif isinstance(func, ast.Attribute):
            func_access.var_access = self.visit_wrapper(func)
            func_access.expr = func_access.var_access.get_expr()
            func_access.name = func.attr
        else:
            pass

        func_args = [self.visit_wrapper(item) for item in node.args]
        func_keywords = [self.visit_wrapper(item) for item in node.keywords]

        expr = f'{func_access.expr}('
        func_args.extend(func_keywords)

        func_access.args.clear()
        for _arg in func_args:
            func_access.args.append(_arg)
            expr = f'{expr}{_arg.get_expr() if isinstance(_arg, VarAccess) else _arg}, '

        if len(func_args) > 0:
            expr = expr[:-2]

        expr = f'{expr})'
        key = f'{expr}:{node.lineno}:{node.col_offset}:{node.end_lineno}:{node.end_col_offset}'

        func_access.set_expr(expr)
        self.s_module.func_access[key] = func_access
        return func_access

    def visit_FormattedValue(self, node: FormattedValue) -> Any:
        """
        节点是以一个 f-字符串形式的格式化字段来代表的。 如果该字符串只包含单个格式化字段而没有任何其他内容则节点可以被隔离，否则它将在 JoinedStr 中出现。

        简言之：format 字符串中的变量/表达式
        :param node:
        :return:
        """
        value_expr = self.visit_wrapper(node.value)
        conversion_expr = node.conversion
        format_spec_expr = self.visit_wrapper(node.format_spec) if node.format_spec else None
        if format_spec_expr is not None or conversion_expr > 0:
            print("")
        return value_expr

    def visit_JoinedStr(self, node: JoinedStr) -> Any:
        """
        一个 f-字符串，由一系列 FormattedValue 和 Constant 节点组成。
        如： f"{a[0]}\t{a[1].name}" for a in extension_mgr.plugins_by_id.items()
        :param node:
        :return:
        """
        _str = model.AstStr(node)
        for item in node.values:
            _str.add_value(self.visit_wrapper(item))
        return _str

    def visit_Constant(self, node: Constant) -> Any:
        literal = LiteralAccess(node)
        literal.set_value(node.value)
        literal.set_expr(type(node.value))
        if isinstance(node.value, str):
            literal.set_expr(f'"{node.value}"')
        else:
            literal.set_expr(node.value)
        return literal

    def visit_NamedExpr(self, node: NamedExpr) -> Any:
        return super().visit_NamedExpr(node)

    def visit_Attribute(self, node: Attribute) -> Any:
        var_access = VarAccess(node)
        var_access.set_label(node.attr)
        var_access.set_var(self.visit_wrapper(node.value))
        return var_access

    def visit_Subscript(self, node: Subscript) -> Any:
        """
        array[0]
        :param node:
        :return:
        """
        var_access = VarAccess(node)
        var_access.set_var(self.visit_wrapper(node.value))
        slice_model = f'{self.visit_wrapper(node.slice)}'
        var_access.set_label(slice_model)
        # if isinstance(node.value, ast.Name):
        #     var_access = self.visit_Name(node.value)
        #     slice_model = self.visit_wrapper(node.slice)
        #     var_access.set_label(f'[{slice_model.expr}]')
        #     var_access.set_expr(f'{var_access.get_var()}{var_access.get_label()}')
        # elif isinstance(node.value, ast.Attribute):
        #     var_access = self.visit_Attribute(node.value)
        #     slice_model = self.visit_wrapper(node.slice)
        #     var_access.set_label(f'{var_access.get_label()}[{slice_model.expr}]')
        #     var_access.set_expr(f'{var_access.get_var()}{var_access.get_label()}')
        # elif isinstance(node.value, ast.Subscript):
        #     var_access = self.visit_Subscript(node.value)
        #     slice_model = self.visit_wrapper(node.slice)
        #     var_access.set_label(f'{var_access.get_label()}[{slice_model.expr}]')
        #     var_access.set_expr(f'{var_access.get_var()}{var_access.get_label()}')
        #     pass
        # else:
        #     value_expr = self.visit_wrapper(node.value)
        #     slice_expr = self.visit_wrapper(node.slice)
        print(var_access)
        return var_access

    def visit_Starred(self, node: Starred) -> Any:
        _var = self.visit_wrapper(node.value)
        # TODO field access
        var_access = VarAccess(node)
        var_access.set_var(self.s_module.global_fields.get(_var.expr))
        var_access.set_args()
        return var_access

    def visit_Name(self, node: Name) -> Any:
        var_access = VarAccess(node)
        var_access.set_var(node.id)
        var_access.set_expr(node.id)
        return var_access

    def visit_List(self, node: List) -> Any:
        return [self.visit_wrapper(item) for item in node.elts]

    def visit_Tuple(self, node: Tuple) -> Any:
        # elts =
        # tuple_expr = "("
        # for elt in elts:
        #     tuple_expr = f'{tuple_expr}{elt.expr}, '
        # tuple_expr = f'{tuple_expr[:-2]})'
        return tuple([self.visit_wrapper(item) for item in node.elts])

    def visit_Del(self, node: Del) -> Any:
        return super().visit_Del(node)

    def visit_Load(self, node: Load) -> Any:
        return super().visit_Load(node)

    def visit_Store(self, node: Store) -> Any:
        return super().visit_Store(node)

    def visit_And(self, node: And) -> Any:
        return 'and'

    def visit_Or(self, node: Or) -> Any:
        return 'or'

    def visit_Add(self, node: Add) -> Any:
        return '+'

    def visit_BitAnd(self, node: BitAnd) -> Any:
        return '&'

    def visit_BitOr(self, node: BitOr) -> Any:
        return '|'

    def visit_BitXor(self, node: BitXor) -> Any:
        return super().visit_BitXor(node)

    def visit_Div(self, node: Div) -> Any:
        return '/'

    def visit_FloorDiv(self, node: FloorDiv) -> Any:
        return '//'

    def visit_LShift(self, node: LShift) -> Any:
        return super().visit_LShift(node)

    def visit_Mod(self, node: Mod) -> Any:
        return '%'

    def visit_Mult(self, node: Mult) -> Any:
        """

        :param node:
        :return:
        """
        return '*'

    def visit_MatMult(self, node: MatMult) -> Any:
        return super().visit_MatMult(node)

    def visit_Pow(self, node: Pow) -> Any:
        return super().visit_Pow(node)

    def visit_RShift(self, node: RShift) -> Any:
        return super().visit_RShift(node)

    def visit_Sub(self, node: Sub) -> Any:
        return '-'

    def visit_Invert(self, node: Invert) -> Any:
        return super().visit_Invert(node)

    def visit_Not(self, node: Not) -> Any:
        return 'not'

    def visit_UAdd(self, node: UAdd) -> Any:
        return super().visit_UAdd(node)

    def visit_USub(self, node: USub) -> Any:
        return '-'

    def visit_Eq(self, node: Eq) -> Any:
        return '=='

    def visit_Gt(self, node: Gt) -> Any:
        return '>'

    def visit_GtE(self, node: GtE) -> Any:
        return '>='

    def visit_In(self, node: In) -> Any:
        return 'in'

    def visit_Is(self, node: Is) -> Any:
        return 'is'

    def visit_IsNot(self, node: IsNot) -> Any:
        return 'is not'

    def visit_Lt(self, node: Lt) -> Any:
        return '<'

    def visit_LtE(self, node: LtE) -> Any:
        return '<='

    def visit_NotEq(self, node: NotEq) -> Any:
        return '!='

    def visit_NotIn(self, node: NotIn) -> Any:
        return 'not in'

    def visit_comprehension(self, node: comprehension) -> Any:
        target_expr = self.visit_wrapper(node.target)
        iter_expr = self.visit_wrapper(node.iter)
        if_expr = [self.visit_wrapper(item) for item in node.ifs]
        is_async = node.is_async
        if len(if_expr) > 0:
            print(if_expr)

        if isinstance(node.target, ast.Tuple):
            _targets = self.visit_Tuple(node.target)
            _target_expr = f'{", ".join([str(_) for _ in _targets])}'
        else:
            _target_expr = target_expr

        return f'async for {_target_expr} in {iter_expr}' if is_async else f'for {_target_expr} in {iter_expr}'

    def visit_ExceptHandler(self, node: ExceptHandler) -> Any:
        """
        一个单独的 except 子句。 type 是它将匹配的异常，通常为一个 Name 节点（或 None 表示捕获全部的 except: 子句）。 name 是一个用于存放异常的别名的原始字符串，或者如果子句没有 as foo 则为 None。 body 为一个节点列表。

        :param node:
        :return:
        """
        err_type = self.visit_wrapper(node.type)
        name_expr = node.name
        body_expr = list()
        for item in node.body:
            _ = self.visit_wrapper(item)
            body_expr.append(str(_))
            pass
        body_expr = '\n\t'.join(body_expr)
        expr = f'except {err_type}'
        if name_expr is not None:
            expr = f'{expr} as {name_expr}'

        expr = f'{expr}:\n\t{body_expr}'
        print(expr)
        return expr

    def visit_arguments(self, node: arguments) -> Any:
        arguments = list()
        for arg in node.args:
            pass

        if isinstance(node.args, list) and isinstance(node.defaults, list):
            if len(node.defaults) > 0 and len(node.args) == len(node.defaults):
                for _arg, default_value in zip(node.args, node.defaults):
                    var_def = self.visit_arg(_arg)
                    var_def.default_value = self.visit_wrapper(default_value)
                    arguments.append(var_def)
            else:
                for _arg in node.args:
                    arguments.append(self.visit_arg(_arg))
        else:
            pass
        return arguments

    def visit_arg(self, node: arg) -> Any:
        arg_name = node.arg
        annotation = node.annotation
        var = VarDef(node)
        var.set_name(arg_name)
        var.annotation = annotation
        if arg_name == 'self':
            var.instance = True
        return var

    def visit_keyword(self, node: keyword) -> Any:
        """
        传给函数调用或类定义的关键字参数。 arg 是形参名称对应的原始字符串，value 是要传入的节点。

        :param node:
        :return:
        """
        arg_expr = node.arg
        value_expr = self.visit_wrapper(node.value)
        expr = f'{arg_expr}={value_expr}'
        print(expr)
        return expr

    def visit_alias(self, node: alias) -> Any:
        return super().visit_alias(node)

    def visit_withitem(self, node: withitem) -> Any:
        context_expr = self.visit_wrapper(node.context_expr)
        vars_expr = self.visit_wrapper(node.optional_vars) if node.optional_vars is not None else None
        if vars_expr is not None:
            vars_expr.add_value(context_expr)
        else:
            return None
        return vars_expr

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

    @staticmethod
    def parse_module(filename: str):
        with open(filename) as f:
            fdata = f.read()
            module = SecurityNodeVisitor(filename, ast.parse(fdata)).get_module()
            return module
