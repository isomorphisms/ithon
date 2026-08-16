"""Type objects shared by Ithon's mandatory static checker."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Type:
    name: str
    args: tuple["Type", ...] = ()

    def __str__(self):
        if self.name == "callable":
            *params, result = self.args
            return f"Callable[[{', '.join(map(str, params))}], {result}]"
        if not self.args:
            return self.name
        return f"{self.name}[{', '.join(map(str, self.args))}]"


UNKNOWN = Type("<unknown>")
NONE = Type("None")
BOOL = Type("bool")
INT = Type("int")
FLOAT = Type("float")
COMPLEX = Type("complex")
STR = Type("str")
BYTES = Type("bytes")
OBJECT = Type("object")
NUMERIC = {BOOL: 0, INT: 1, FLOAT: 2, COMPLEX: 3}


def assignable(actual, expected):
    if expected == OBJECT or actual == expected or actual == UNKNOWN:
        return True
    if actual in NUMERIC and expected in NUMERIC:
        return NUMERIC[actual] <= NUMERIC[expected]
    return actual.name == expected.name and actual.args == expected.args
