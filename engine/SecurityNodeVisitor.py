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
from model.func_access import FuncAccess
from model.literal_access import LiteralAccess
from model.s_field import SField
from model.var_access import VarAccess


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
        func_name = node.name
        func_args = self.visit_wrapper(node.args)
        func_body = [self.visit_wrapper(item) for item in node.body]
        func_decorator_list = [self.visit_wrapper(item) for item in node.decorator_list]
        func_returns = self.visit_wrapper(node.returns) if node.returns else None
        func_type_comment = self.visit_wrapper(node.type_comment) if node.type_comment else None
        self.s_module.funcs[func_name] = node

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Any:
        return super().visit_AsyncFunctionDef(node)

    def visit_ClassDef(self, node: ClassDef) -> Any:
        return super().visit_ClassDef(node)

    def visit_Return(self, node: Return) -> Any:
        value = self.visit_wrapper(node.value)
        return f'return {value}'

    def visit_Delete(self, node: Delete) -> Any:
        return super().visit_Delete(node)

    def visit_field(self, field, value):
        s_field = SField()
        s_field.name = self.visit_wrapper(field)
        s_field_value = self.visit_wrapper(value)
        s_field.expr = f'{s_field.name} = {s_field_value}'
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
        return s_fields if len(s_fields) > 1 else s_fields[0]

    def visit_AugAssign(self, node: AugAssign) -> Any:
        return super().visit_AugAssign(node)

    def visit_AnnAssign(self, node: AnnAssign) -> Any:
        return super().visit_AnnAssign(node)

    def visit_For(self, node: For) -> Any:
        # target
        loop_var = self.visit_wrapper(node.target)
        # iter
        loop_iter = self.visit_wrapper(node.iter)
        expr = f'for {loop_var} in {loop_iter}:'
        # body
        loop_body = [self.visit_wrapper(item) for item in node.body]
        for body in loop_body:
            expr = f'{expr}\n\t{body}'
        # orelse
        loop_else = [self.visit_wrapper(item) for item in node.orelse]
        expr = expr if len(loop_else) == 0 else f'{expr}\nelse:'
        for body in loop_else:
            expr = f'{expr}\n\t{body}'
        print(expr)
        return expr

    def visit_AsyncFor(self, node: AsyncFor) -> Any:
        return super().visit_AsyncFor(node)

    def visit_While(self, node: While) -> Any:
        return super().visit_While(node)

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
        return expr

    def visit_AsyncWith(self, node: AsyncWith) -> Any:
        return super().visit_AsyncWith(node)

    def visit_Raise(self, node: Raise) -> Any:
        cause_expr = self.visit_wrapper(node.cause) if node.cause else None
        exc_expr = self.visit_wrapper(node.exc)
        if cause_expr is not None:
            pass
        return f'raise {exc_expr}'

    def visit_Try(self, node: Try) -> Any:
        """
        try 代码块。 所有属性都是要执行的节点列表，除了 handlers，它是一个 ExceptHandler 节点列表。

        :param node:
        :return:
        """
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
        return expr

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
        return 'pass'

    def visit_Break(self, node: Break) -> Any:
        return super().visit_Break(node)

    def visit_Continue(self, node: Continue) -> Any:
        return super().visit_Continue(node)

    def visit_Slice(self, node: Slice) -> Any:
        return super().visit_Slice(node)

    def visit_BoolOp(self, node: BoolOp) -> Any:
        op_expr = self.visit_wrapper(node.op)
        value_exprs = [self.visit_wrapper(item) for item in node.values]
        expr = ''
        for value_expr in value_exprs:
            if isinstance(value_expr, list):
                expr = f'{expr} or {str(value_expr)}'
            else:
                expr = f'{expr} or {value_expr}'
        return expr[2:]

    def visit_BinOp(self, node: BinOp) -> Any:
        """
        双目运算（如相加或相减）。 op 是运算符，而 left 和 right 是任意表达式节点。

        :param node:
        :return:
        """
        left_expr = self.visit_wrapper(node.left)
        op_expr = self.visit_wrapper(node.op)
        right_expr = self.visit_wrapper(node.right)
        expr = f'{left_expr} {op_expr} {right_expr}'
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
        return super().visit_Set(node)

    def visit_ListComp(self, node: ListComp) -> Any:
        body_expr = self.visit_wrapper(node.elt)
        generator_expr = [self.visit_wrapper(item) for item in node.generators]
        return f'[{body_expr} {" ".join(generator_expr)}]'

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
        left = node.left
        ops = node.ops
        comparators = node.comparators
        left_expr = self.visit_wrapper(left)
        op_exprs = [self.visit_wrapper(op) for op in ops]
        comparators = [self.visit_wrapper(comparator) for comparator in comparators]
        full_expr = f'{left_expr} {" ".join(op_exprs)} {" ".join(comparators)}'
        self.s_module.expr[full_expr] = node
        return full_expr

    def visit_Call(self, node: Call) -> Any:
        func_access = FuncAccess(node.lineno, node.end_lineno, node.col_offset, node.end_col_offset)
        func_access.set_node(node)

        expr = ""
        func = node.func
        func_name = ""

        func_access.var_access = self.visit_wrapper(func)
        func_name = func_access.var_access.get_expr()
        if isinstance(func, ast.Attribute):
            # TODO func.value 可能是复杂接口，需要拆分至独立的 var
            func_access.label = func.attr
            func_access.var_access.set_expr(func_access.var_access.get_var())
            func_access.var_access.set_label("")
            func_name = f'{func_access.var_access.get_expr()}.{func.attr}'
        else:
            pass

        func_args = [self.visit_wrapper(item) for item in node.args]
        func_keywords = [self.visit_wrapper(item) for item in node.keywords]

        expr = f'{func_name}('
        func_args.extend(func_keywords)

        for _arg in func_args:
            func_access.args.append(_arg)
            expr = f'{expr}{_arg.get_expr() if isinstance(_arg, VarAccess) else _arg}, '

        if len(func_args) > 0:
            expr = expr[:-2]

        expr = f'{expr})'
        key = f'{expr}:{node.lineno}:{node.col_offset}:{node.end_lineno}:{node.end_col_offset}'

        func_access.set_expr(expr)
        self.s_module.func_access[key] = func_access
        return expr

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
        value_exprs = [self.visit_wrapper(item) for item in node.values]
        expr = ''.join(value_exprs)
        return f'f{expr}'

    def visit_Constant(self, node: Constant) -> Any:
        literal = LiteralAccess(node.lineno, node.end_lineno, node.col_offset, node.end_col_offset)
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
        if isinstance(node.value, ast.Name):
            var_access = self.visit_wrapper(node.value)
            var_access.set_label(node.attr)
            var_access.set_expr(f'{var_access.get_expr()}.{node.attr}')
        elif isinstance(node.value, ast.Attribute):
            var_access = self.visit_Attribute(node.value)
            var_access.set_label(f'{var_access.get_label()}.{node.attr}')
            var_access.set_expr(f'{var_access.get_var()}.{var_access.get_label()}')
            print()
        elif isinstance(node.value, ast.Subscript):
            var_access = self.visit_Subscript(node.value)
            var_access.set_label(f'{var_access.get_label()}.{node.attr}')
            var_access.set_expr(f'{var_access.get_var()}{var_access.get_label()}')
            print()
        else:
            print()

        attr = node.attr
        value = self.visit_wrapper(node.value) if node.value else None
        return var_access

    def visit_Subscript(self, node: Subscript) -> Any:
        """
        array[0]
        :param node:
        :return:
        """
        if isinstance(node.value, ast.Name):
            var_access = self.visit_Name(node.value)
            var_access.set_label(self.visit_wrapper(node.slice))
            var_access.set_expr(f'{var_access.get_var()}[{var_access.get_label()}]')
        else:
            value_expr = self.visit_wrapper(node.value)
            slice_expr = self.visit_wrapper(node.slice)
        return var_access

    def visit_Starred(self, node: Starred) -> Any:
        return super().visit_Starred(node)

    def visit_Name(self, node: Name) -> Any:
        var_access = VarAccess(node.lineno, node.end_lineno, node.col_offset, node.end_col_offset)
        var_access.set_var(node.id)
        var_access.set_expr(node.id)
        return var_access

    def visit_List(self, node: List) -> Any:
        list_values = [self.visit_wrapper(item) for item in node.elts]
        return list_values if list_values else []

    def visit_Tuple(self, node: Tuple) -> Any:
        var_names = [self.visit_wrapper(item) for item in node.elts]
        return f'{", ".join(var_names)}'

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
        return super().visit_BitAnd(node)

    def visit_BitOr(self, node: BitOr) -> Any:
        return super().visit_BitOr(node)

    def visit_BitXor(self, node: BitXor) -> Any:
        return super().visit_BitXor(node)

    def visit_Div(self, node: Div) -> Any:
        return '/'

    def visit_FloorDiv(self, node: FloorDiv) -> Any:
        return super().visit_FloorDiv(node)

    def visit_LShift(self, node: LShift) -> Any:
        return super().visit_LShift(node)

    def visit_Mod(self, node: Mod) -> Any:
        return super().visit_Mod(node)

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
        return super().visit_USub(node)

    def visit_Eq(self, node: Eq) -> Any:
        return '=='

    def visit_Gt(self, node: Gt) -> Any:
        return '>'

    def visit_GtE(self, node: GtE) -> Any:
        return super().visit_GtE(node)

    def visit_In(self, node: In) -> Any:
        return 'in'

    def visit_Is(self, node: Is) -> Any:
        return 'is'

    def visit_IsNot(self, node: IsNot) -> Any:
        return 'is not'

    def visit_Lt(self, node: Lt) -> Any:
        return super().visit_Lt(node)

    def visit_LtE(self, node: LtE) -> Any:
        return super().visit_LtE(node)

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
        return f'async for {target_expr} in {iter_expr}' if is_async else f'for {target_expr} in {iter_expr}'

    def visit_ExceptHandler(self, node: ExceptHandler) -> Any:
        """
        一个单独的 except 子句。 type 是它将匹配的异常，通常为一个 Name 节点（或 None 表示捕获全部的 except: 子句）。 name 是一个用于存放异常的别名的原始字符串，或者如果子句没有 as foo 则为 None。 body 为一个节点列表。

        :param node:
        :return:
        """
        err_type = self.visit_wrapper(node.type)
        name_expr = node.name
        body_expr = '\n\t'.join(self.visit_wrapper(item) for item in node.body)
        expr = f'except {err_type}'
        if name_expr is not None:
            expr = f'{expr} as {name_expr}'

        expr = f'{expr}:\n\t{body_expr}'
        print(expr)
        return expr

    def visit_arguments(self, node: arguments) -> Any:
        arguments = list()
        if isinstance(node.args, list) and isinstance(node.defaults, list):
            if len(node.defaults) > 0 and len(node.args) == len(node.defaults):
                for arg_name, default_value in zip(node.args, node.defaults):
                    arguments.append(f'{self.visit_wrapper(arg_name)}={self.visit_wrapper(default_value)}')
            else:
                for arg in node.args:
                    arguments.append(f'{self.visit_wrapper(arg)}')
        else:
            pass
        return ', '.join(arguments)

    def visit_arg(self, node: arg) -> Any:
        arg = node.arg
        annotation = node.annotation
        type_comment = node.type_comment
        expr = ''
        if annotation:
            expr = f'{annotation}'
        expr = f'{expr} {arg}' if expr else arg
        expr = f'{expr}:{type_comment}' if type_comment else expr
        return expr

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
        vars_expr = self.visit_wrapper(node.optional_vars)
        return f'{context_expr} as {vars_expr}'

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
        print(f'func access: {len(nv.s_module.func_access)}')
        print(ast.dump(s_module, indent=4))
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
    filename = '/Users/owefsad/PycharmProjects/tk-example/main.py'
    filename = '/Users/owefsad/PycharmProjects/bandit/bandit/core/blacklisting.py'
    s = SecurityNodeVisitor()
    with open(filename) as f:
        fdata = f.read()
        module_meta = s.visit_module(fdata)
        print(module_meta)
