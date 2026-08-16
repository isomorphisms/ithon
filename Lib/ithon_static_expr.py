"""Expression inference for Ithon's mandatory static checker."""
import ast

from ithon_static_types import (
    BOOL, BYTES, COMPLEX, FLOAT, INT, NONE, NUMERIC, STR, UNKNOWN, Type,
)


class ExprMixin:
    def expr(self, node, expected=None):
        if isinstance(node, ast.Constant):
            value = node.value
            if value is None:
                return NONE
            if isinstance(value, bool):
                return BOOL
            if isinstance(value, int):
                return INT
            if isinstance(value, float):
                return FLOAT
            if isinstance(value, complex):
                return COMPLEX
            if isinstance(value, str):
                return STR
            if isinstance(value, bytes):
                return BYTES
        if isinstance(node, ast.Name):
            typ = self.get(node.id)
            if typ is None:
                self.error(node, f"name '{node.id}' has no static type")
            return typ
        if isinstance(node, ast.BinOp):
            left, right = self.expr(node.left), self.expr(node.right)
            if left in NUMERIC and right in NUMERIC:
                typ = left if NUMERIC[left] >= NUMERIC[right] else right
                return FLOAT if isinstance(node.op, ast.Div) and typ != COMPLEX else typ
            if isinstance(node.op, ast.Add) and left == right and left in (STR, BYTES):
                return left
            if isinstance(node.op, ast.Mult) and left in (STR, BYTES) and right in (BOOL, INT):
                return left
            if isinstance(node.op, ast.Mult) and right in (STR, BYTES) and left in (BOOL, INT):
                return right
            self.error(node, f"operator is not statically defined for {left} and {right}")
        if isinstance(node, ast.UnaryOp):
            return self.expr(node.operand)
        if isinstance(node, ast.Compare):
            self.expr(node.left)
            for item in node.comparators:
                self.expr(item)
            return BOOL
        if isinstance(node, ast.BoolOp):
            for item in node.values:
                self.expr(item)
            return BOOL
        if isinstance(node, ast.IfExp):
            self.expr(node.test)
            left, right = self.expr(node.body), self.expr(node.orelse)
            return left if left == right else UNKNOWN
        if isinstance(node, ast.List):
            if not node.elts:
                if expected and expected.name == "list":
                    return expected
                self.error(node, "empty list needs an explicit element type")
            types = [self.expr(item) for item in node.elts]
            if any(typ != types[0] for typ in types):
                self.error(node, "list elements need one static type")
            return Type("list", (types[0],))
        if isinstance(node, ast.Tuple):
            return Type("tuple", tuple(self.expr(item) for item in node.elts))
        if isinstance(node, ast.Dict):
            if not node.keys:
                if expected and expected.name == "dict":
                    return expected
                self.error(node, "empty dict needs explicit key/value types")
            keys = [self.expr(item) for item in node.keys]
            values = [self.expr(item) for item in node.values]
            if any(typ != keys[0] for typ in keys) or any(typ != values[0] for typ in values):
                self.error(node, "dict keys/values need stable static types")
            return Type("dict", (keys[0], values[0]))
        if isinstance(node, ast.Lambda):
            if expected is None or expected.name != "callable":
                self.error(node, "lambda needs a contextual Callable")
            params, result = expected.args[:-1], expected.args[-1]
            args = [*node.args.posonlyargs, *node.args.args]
            if len(args) != len(params):
                self.error(node, "lambda parameter count does not match Callable")
            self.scopes.append({arg.arg: typ for arg, typ in zip(args, params)})
            actual = self.expr(node.body, result)
            self.require(actual, result, node.body)
            self.scopes.pop()
            return expected
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "range":
                for arg in node.args:
                    self.require(self.expr(arg), INT, arg)
                return Type("range")
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                for arg in node.args:
                    self.expr(arg)
                return NONE
            callee = self.expr(node.func)
            if callee.name == "type":
                for arg in node.args:
                    self.expr(arg)
                return callee.args[0]
            if callee.name == "callable":
                params, result = callee.args[:-1], callee.args[-1]
                if len(node.args) != len(params):
                    self.error(node, f"call expects {len(params)} arguments, got {len(node.args)}")
                for arg, typ in zip(node.args, params):
                    self.require(self.expr(arg, typ), typ, arg)
                return result
            if callee in (Type("module"), UNKNOWN) or callee.name == "external":
                for arg in node.args:
                    self.expr(arg)
                return UNKNOWN
            self.error(node.func, f"{callee} is not statically callable")
        if isinstance(node, ast.Attribute):
            self.expr(node.value)
            return UNKNOWN
        self.error(node, f"cannot infer static type of {type(node).__name__}")

    @staticmethod
    def iter_type(typ):
        if typ.name in ("list", "set") and typ.args:
            return typ.args[0]
        if typ.name == "range":
            return INT
        if typ == STR:
            return STR
        if typ == BYTES:
            return INT
        return UNKNOWN
