"""Ithon surface syntax lowering and mandatory static checking.

The public surface uses ∈ / ∋ for typed bindings. CPython-style colon
annotations are deliberately not part of Ithon's typing syntax.
"""
from __future__ import annotations

import ast
import re

from ithon_static import BOOL, STR, Checker, StaticTypeError

_NAME = re.compile(r"^[A-Za-z_]\w*$", re.UNICODE)


def _error(filename: str, line_number: int, line: str, message: str) -> StaticTypeError:
    return StaticTypeError(message, (filename, line_number, 1, line))


def _scan_top_level(text: str, wanted: str) -> int:
    """Return the first top-level occurrence of one character, or -1."""
    stack: list[str] = []
    quote: str | None = None
    escaped = False
    pairs = {')': '(', ']': '[', '}': '{'}
    for i, ch in enumerate(text):
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch in "([{":
            stack.append(ch)
            continue
        if ch in ")]}":
            if stack and stack[-1] == pairs[ch]:
                stack.pop()
            continue
        if not stack and ch == wanted:
            return i
    return -1


def _split_top_level(text: str, delimiter: str) -> list[str]:
    pieces: list[str] = []
    start = 0
    stack: list[str] = []
    quote: str | None = None
    escaped = False
    pairs = {')': '(', ']': '[', '}': '{'}
    for i, ch in enumerate(text):
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch in "([{":
            stack.append(ch)
            continue
        if ch in ")]}":
            if stack and stack[-1] == pairs[ch]:
                stack.pop()
            continue
        if not stack and ch == delimiter:
            pieces.append(text[start:i])
            start = i + 1
    pieces.append(text[start:])
    return pieces


def _binding(text: str, filename: str, line_number: int, line: str) -> str | None:
    """Lower `name ∈ Type` or `Type ∋ name` to the AST annotation spelling."""
    stripped = text.strip()
    in_pos = _scan_top_level(stripped, "∈")
    ni_pos = _scan_top_level(stripped, "∋")
    if in_pos >= 0 and ni_pos >= 0:
        raise _error(filename, line_number, line, "a typed binding uses one of ∈ or ∋, not both")
    if in_pos >= 0:
        name = stripped[:in_pos].strip()
        typ = stripped[in_pos + 1:].strip()
        if not _NAME.match(name) or not typ:
            raise _error(filename, line_number, line, "left side of ∈ must be a binding name")
        return f"{name}: {typ}"
    if ni_pos >= 0:
        typ = stripped[:ni_pos].strip()
        name = stripped[ni_pos + 1:].strip()
        if not _NAME.match(name) or not typ:
            raise _error(filename, line_number, line, "right side of ∋ must be a binding name")
        return f"{name}: {typ}"
    return None


def _reject_colon_binding(text: str, filename: str, line_number: int, line: str) -> None:
    if _scan_top_level(text, ":") >= 0:
        raise _error(filename, line_number, line, "Ithon type membership uses ∈ or ∋, not :")


def _matching_paren(text: str, opening: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    for i in range(opening, len(text)):
        ch = text[i]
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _lower_function(line: str, filename: str, line_number: int) -> str:
    opening = line.find("(")
    if opening < 0:
        return line
    closing = _matching_paren(line, opening)
    if closing < 0:
        return line

    params = line[opening + 1:closing]
    lowered_params: list[str] = []
    for raw in _split_top_level(params, ","):
        if not raw.strip():
            lowered_params.append(raw)
            continue
        prefix = ""
        body = raw.strip()
        if body.startswith("**"):
            prefix, body = "**", body[2:].strip()
        elif body.startswith("*"):
            prefix, body = "*", body[1:].strip()
        eq = _scan_top_level(body, "=")
        default = ""
        if eq >= 0:
            default = body[eq:]
            body = body[:eq].strip()
        lowered = _binding(body, filename, line_number, line)
        if lowered is None:
            _reject_colon_binding(body, filename, line_number, line)
            lowered = prefix + body
        else:
            lowered = prefix + lowered
        lowered_params.append(lowered + default)

    tail = line[closing + 1:]
    if "->" in tail:
        raise _error(filename, line_number, line, "Ithon return types use →, not ->")
    arrow = _scan_top_level(tail, "→")
    if arrow >= 0:
        tail = tail[:arrow] + "->" + tail[arrow + 1:]
    return line[:opening + 1] + ", ".join(lowered_params) + ")" + tail


def _find_assignment(text: str) -> tuple[int, str] | None:
    for op in ("←", "→", "="):
        pos = _scan_top_level(text, op)
        if pos >= 0:
            if op == "=" and pos + 1 < len(text) and text[pos + 1] == "=":
                continue
            return pos, op
    return None


def _lower_membership_expression(text: str) -> str:
    """Lower ordinary membership after typed-binding positions are removed."""
    text = text.replace("∈", "in")
    atom = r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*"
    pattern = re.compile(rf"({atom})\s*∋\s*({atom})")
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub(lambda m: f"{m.group(2)} in {m.group(1)}", text)
    return text


def _lower_line(line: str, filename: str, line_number: int) -> str:
    stripped = line.lstrip()
    if stripped.startswith("def ") or stripped.startswith("async def "):
        return _lower_function(line, filename, line_number)

    assignment = _find_assignment(line)
    if assignment is None:
        if "∈" in line or "∋" in line:
            return _lower_membership_expression(line)
        if re.match(r"^\s*[A-Za-z_]\w*\s*:\s*[^:]+$", line):
            raise _error(filename, line_number, line, "Ithon type membership uses ∈ or ∋, not :")
        return line

    pos, op = assignment
    left, right = line[:pos], line[pos + len(op):]

    if op == "→":
        binding = _binding(right, filename, line_number, line)
        if binding is not None:
            indent = left[: len(left) - len(left.lstrip())]
            value = _lower_membership_expression(left.strip())
            return f"{indent}{binding} ← {value}"
        return line[:pos + len(op)] + _lower_membership_expression(right)

    binding = _binding(left, filename, line_number, line)
    if binding is not None:
        if op == "=":
            raise _error(filename, line_number, line, "Ithon assignment uses ← or →, not =")
        indent = left[: len(left) - len(left.lstrip())]
        return f"{indent}{binding} {op} {_lower_membership_expression(right.strip())}"

    _reject_colon_binding(left.strip(), filename, line_number, line)
    return line[:pos + len(op)] + _lower_membership_expression(right)


def lower_source(source: str, filename: str = "<ithon>") -> str:
    """Lower Ithon's membership surface syntax to the existing AST substrate."""
    lines = source.splitlines(keepends=True)
    out: list[str] = []
    for number, physical in enumerate(lines, 1):
        newline = "\n" if physical.endswith("\n") else ""
        line = physical[:-1] if newline else physical
        out.append(_lower_line(line, filename, number) + newline)
    return "".join(out)


class IthonChecker(Checker):
    def infer(self, node: ast.AST, expected=None):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.In):
            left = self.infer(node.left)
            right = self.infer(node.comparators[0])
            if right.name == "type" and right.args:
                self.require(left, right.args[0], node.left)
            elif right.name in {"list", "set", "tuple", "frozenset"} and right.args:
                self.require(left, right.args[0], node.left)
            elif right == STR:
                self.require(left, STR, node.left)
            return BOOL
        return super().infer(node, expected)


def check_source(source: str, filename: str = "<ithon>") -> ast.Module:
    lowered = lower_source(source, filename)
    tree = ast.parse(lowered, filename=filename, mode="exec")
    checker = IthonChecker(source, filename)
    checker.check(tree)
    return tree


def check_file(path: str) -> ast.Module:
    with open(path, "r", encoding="utf-8") as handle:
        return check_source(handle.read(), path)
