# Ithon Unicode syntax

This branch names the first implemented Ithon language slice already present in the imported CPython-derived tree.

Current syntax includes:

```text
x ← value       left assignment
value → x       right assignment / rightward data flow
×               multiplication
•               multiplication
·               multiplication
÷               division
λ x: expr       anonymous function
ƒ x: expr       anonymous function
```

Assignment arrows can chain in the supported direction, and annotated left assignment preserves Python's annotated-assignment AST form.

Unicode arithmetic operators are arithmetic operators only. In particular, `×` must not replace `*` where `*` means unpacking, varargs, or another non-multiplication grammar construct.

The existing compatibility slice still accepts ordinary Python spellings such as `=` for assignment, `*` for multiplication, `/` for division, and `lambda`. Later Ithon branches may deliberately narrow compatibility; compatibility with upstream Python is not a governing design constraint.

The focused executable tests for this slice live in `Lib/test/test_ithon_syntax.py`.
