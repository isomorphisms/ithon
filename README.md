# i-thon

ithon  
python with assignment arrows

companion to ick, icky, grease, ir, idriç

meant to be written with a programmers keyboard

## static typing

Ithon is statically typed. Types are inferred when the result is unambiguous:

```python
x ← 42
x ← 43       # int stays int
x ← "wrong"  # static type error; the program does not start
```

Function boundaries are explicit:

```python
def double(x: int) -> int:
    return x × 2
```

A value whose type cannot be inferred at a Python/foreign-library boundary
needs an annotation. Lambdas similarly need a contextual `Callable` type.

`./ithon program.ithon` checks the complete module before executing it.
Imported `.ithon` modules are checked by the Ithon loader; ordinary `.py`
modules remain foreign Python libraries.
