# Ithon mandatory static typing

Ithon is statically typed. Static typing is not an optional lint mode layered on top of a dynamically typed language.

The initial implementation may reuse CPython's parser, AST, runtime, and object model, but an Ithon module must be statically checked as a complete module before any of its code executes.

## Core rules

- There is no implicit `Any`.
- An assignment with an unambiguous value may infer its type.
- Once a name has a static type, later assignment must preserve that type.
- An explicitly annotated assignment must match its annotation.
- Numeric widening may be accepted where the target type explicitly permits it, for example assigning an integer value to a `float` binding.
- Function parameters require static types.
- Function results require static types. `__init__` may infer `None` as its result.
- Function bodies and local calls are checked against those signatures.
- Lambda parameters may be inferred from an explicit contextual `Callable[[...], result]` type. A lambda without enough contextual type information is rejected rather than silently becoming dynamic.
- Empty containers require enough context to determine their element/key/value types.
- Imports from foreign Python libraries do not silently inject dynamic values into Ithon. If the checker cannot determine a foreign result's type, the Ithon binding needs an explicit type boundary.
- Star imports are rejected when they make bindings statically unknowable.
- Unsupported constructs fail as unsupported static typing rather than quietly falling back to dynamic execution.

Representative intended behavior:

```python
x = 42
x = 43                 # accepted
x = "forty two"        # rejected

x: float = 42           # accepted
x: int = 4.2            # rejected

def double(x: int) -> int:
    return x * 2

double("21")           # rejected

double_fn: Callable[[int], int] = lambda x: x * 2

import math
root: float = math.sqrt(4.0)
```

The checker should finish checking the entire module before execution begins, so an error later in a file cannot occur after earlier top-level statements have already produced side effects.

## Relation to Python

Python compatibility is useful as an implementation and library bridge, not as a requirement that Ithon preserve Python's dynamic semantics. Ordinary `.py` source is foreign Python. Ithon source uses `.pi`; that naming decision is tracked independently on `feature/pi-source-files`.

The CPython tree is an implementation substrate and source/reference pool. Ithon changes do not need to be structured as patches suitable for acceptance by Python upstream.

## Later type-system work

Mandatory static typing is the floor, not the ceiling. Refinements, dependent facts, indexed quantities such as `Bits[n]`, proofs about bounds and widths, and representation selection belong to later type-system passes and are tracked separately on `feature/dependent-refinement-types`.
