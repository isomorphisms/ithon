"""Mandatory static checking for Ithon source."""
from __future__ import annotations

import ast

from ithon_static_expr import ExprMixin
from ithon_static_types import (
    BOOL, BYTES, COMPLEX, FLOAT, INT, NONE, OBJECT, STR, UNKNOWN, Type, assignable,
)


class StaticTypeError(SyntaxError):
    pass


class Checker(ExprMixin):
    def __init__(self, source, filename):
        self.source = source
        self.filename = filename
        self.lines = source.splitlines()
        self.scopes = [self._builtins()]
        self.returns = []

    @staticmethod
    def _builtins():
        return {
            "int": Type("type", (INT,)),
            "float": Type("type", (FLOAT,)),
            "complex": Type("type", (COMPLEX,)),
            "bool": Type("type", (BOOL,)),
            "str": Type("type", (STR,)),
            "bytes": Type("type", (BYTES,)),
            "object": Type("type", (OBJECT,)),
            "range": Type("range-fn"),
            "print": Type("print-fn"),
            "len": Type("callable", (OBJECT, INT)),
        }

    def error(self, node, message):
        line = getattr(node, "lineno", 1)
        column = getattr(node, "col_offset", 0) + 1
        text = self.lines[line - 1] if 0 < line <= len(self.lines) else None
        raise StaticTypeError(message, (self.filename, line, column, text))

    def get(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def set(self, name, typ):
        self.scopes[-1][name] = typ

    def annotation(self, node):
        if node is None:
            return UNKNOWN
        if isinstance(node, ast.Name):
            return {
                "int": INT, "float": FLOAT, "complex": COMPLEX, "bool": BOOL,
                "str": STR, "bytes": BYTES, "object": OBJECT, "None": NONE,
            }.get(node.id, Type(node.id))
        if isinstance(node, ast.Constant) and node.value is None:
            return NONE
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return Type("union", (self.annotation(node.left), self.annotation(node.right)))
        if isinstance(node, ast.Subscript):
            base = node.value.id if isinstance(node.value, ast.Name) else None
            if base == "Callable":
                if not isinstance(node.slice, ast.Tuple) or len(node.slice.elts) != 2:
                    self.error(node, "Callable must be Callable[[args...], result]")
                params, result = node.slice.elts
                if not isinstance(params, (ast.List, ast.Tuple)):
                    self.error(params, "Callable parameter types must be in brackets")
                return Type(
                    "callable",
                    tuple(self.annotation(item) for item in params.elts)
                    + (self.annotation(result),),
                )
            if base:
                args = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
                return Type(base, tuple(self.annotation(item) for item in args))
        self.error(node, "unsupported static type annotation")

    def require(self, actual, expected, node):
        if not assignable(actual, expected):
            self.error(node, f"expected {expected}, got {actual}")

    def check(self, tree):
        for stmt in tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.declare_function(stmt)
        for stmt in tree.body:
            self.stmt(stmt)

    def declare_function(self, node):
        params = []
        for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            if arg.annotation is None:
                self.error(arg, f"parameter '{arg.arg}' needs a static type")
            params.append(self.annotation(arg.annotation))
        if node.args.vararg:
            if node.args.vararg.annotation is None:
                self.error(node.args.vararg, f"parameter '*{node.args.vararg.arg}' needs a static type")
            params.append(Type("vararg", (self.annotation(node.args.vararg.annotation),)))
        if node.args.kwarg:
            if node.args.kwarg.annotation is None:
                self.error(node.args.kwarg, f"parameter '**{node.args.kwarg.arg}' needs a static type")
            params.append(Type("kwarg", (self.annotation(node.args.kwarg.annotation),)))
        if node.returns is None:
            self.error(node, f"function '{node.name}' needs a return type")
        self.set(node.name, Type("callable", tuple(params) + (self.annotation(node.returns),)))

    def stmt(self, node):
        if isinstance(node, ast.Assign):
            actual = self.expr(node.value)
            if actual == UNKNOWN:
                self.error(node.value, "cannot infer assignment type; add an annotation")
            for target in node.targets:
                self.assign(target, actual)
            return
        if isinstance(node, ast.AnnAssign):
            expected = self.annotation(node.annotation)
            if node.value is not None:
                actual = self.expr(node.value, expected)
                self.require(actual, expected, node.value)
            self.assign(node.target, expected, annotated=True)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            signature = self.get(node.name)
            params, result = signature.args[:-1], signature.args[-1]
            self.scopes.append({})
            args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            for arg, typ in zip(args, params):
                self.set(arg.arg, typ)
            self.returns.append(result)
            for stmt in node.body:
                self.stmt(stmt)
            self.returns.pop()
            self.scopes.pop()
            return
        if isinstance(node, ast.Return):
            if not self.returns:
                self.error(node, "return outside typed function")
            actual = NONE if node.value is None else self.expr(node.value, self.returns[-1])
            self.require(actual, self.returns[-1], node)
            return
        if isinstance(node, ast.Expr):
            self.expr(node.value)
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                self.set(alias.asname or alias.name.split(".")[0], Type("module"))
            return
        if isinstance(node, ast.For):
            item = self.iter_type(self.expr(node.iter))
            if item == UNKNOWN:
                self.error(node.iter, "cannot infer loop target type")
            self.assign(node.target, item)
            for stmt in node.body + node.orelse:
                self.stmt(stmt)
            return
        if isinstance(node, ast.If):
            self.expr(node.test)
            for stmt in node.body + node.orelse:
                self.stmt(stmt)
            return
        if isinstance(node, ast.While):
            self.expr(node.test)
            for stmt in node.body + node.orelse:
                self.stmt(stmt)
            return
        if isinstance(node, (ast.Pass, ast.Break, ast.Continue)):
            return
        self.error(node, f"static checking for {type(node).__name__} is not implemented")

    def assign(self, node, typ, annotated=False):
        if not isinstance(node, ast.Name):
            self.error(node, "typed assignment currently requires a name target")
        old = self.get(node.id)
        if old is not None and old not in self._builtins().values() and not annotated:
            if not assignable(typ, old):
                self.error(node, f"assignment to '{node.id}' expects {old}, got {typ}")
            typ = old
        self.set(node.id, typ)


def check_source(source, filename="<ithon>"):
    tree = ast.parse(source, filename=filename, mode="exec")
    Checker(source, filename).check(tree)
    return tree


def check_file(path):
    with open(path, encoding="utf-8") as handle:
        return check_source(handle.read(), path)
