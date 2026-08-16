# Ithon mathematical semantics

Ithon should not silently inherit ordinary Python numerical semantics where those semantics conflict with the mathematical language we want.

The mathematical type system states what an object is. The compiler may choose a cheaper representation only when it can prove that the representation preserves the exact value and intended operations.

## Macaulay2 debt and attribution

Where applicable, Ithon deliberately follows Macaulay2's mathematical semantics as closely as practical. Macaulay2 was originally written by Dan Grayson and Mike Stillman; David Eisenbud later joined the project, together with many package authors and contributors.

Project and source references:

- https://macaulay2.com/
- https://github.com/Macaulay2/M2
- https://github.com/Macaulay2/M2/blob/stable/CITATION.cff

When an Ithon-owned implementation follows a Macaulay2 semantic choice, keep that debt visible near the implementation. If source code is actually copied rather than merely following public mathematical/language behavior, preserve the applicable authorship, provenance, copyright, and license notices.

## Exact division and rational numbers

Ordinary mathematical division is exact:

```text
84 ÷ 2 = 42
85 ÷ 2 = 85/2
```

The type rule should be mathematically equivalent to:

```text
Integer  ÷ Integer  -> Rational
Rational ÷ Rational -> Rational
```

A rational whose denominator is one may print or execute with an integer representation without ceasing to be the exact rational value. Floating-point approximation must be explicit.

Integer quotient, remainder, `divmod`, floor, ceiling, and rounding are separate operations. Their usefulness is not a reason to make `÷` mean floor division or floating approximation.

GMP or FLINT rational arithmetic are natural implementations to test. Correctness and coherent semantics come before representation tricks; lazy normalization is an optimization question, not a semantic difference.

## Rings, fields, and polynomial rings

Initial direction:

```text
ZZ                 integers
QQ = frac ZZ       rationals
R[x]               polynomial ring over R
R[x, y, z]         multivariate polynomial ring
frac R             fraction field of an integral domain R
```

Polynomial rings are an early target. Sparse maps from monomials to coefficients are one possible representation, not part of the language-level definition. Gröbner bases, resolutions, and more advanced computer-algebra machinery can follow after the basic ring semantics are sound.

## Square roots and complex numbers

Square root may enlarge the mathematical domain rather than fail merely because a radicand is negative:

```text
√−1 = complex(imaginary=1)
```

The exact result is the positive imaginary unit. Tests should pin both the value and equality with an explicitly constructed complex number having real part zero and imaginary part one.

Mathematical complex-number semantics must remain separate from any chosen Cartesian or polar machine representation.

## Membership in both directions

Both ordinary mathematical spellings are useful:

```text
x ∈ A
A ∋ x
```

They express the same membership relation with the operands written in opposite orders. The parser should preserve which spelling was written; later semantic elaboration may reduce them to one relation.

## Infinity

Reserve `∞` and Unicode minus `−` so extended ordered values can express:

```text
−∞ < x < ∞
```

for every finite ordered real-like value `x`.

Infinity and negative infinity are not ordinary rational numbers. Expressions such as `∞ − ∞`, `0 × ∞`, and `∞ ÷ ∞` must not be assigned arbitrary numerical answers merely to keep execution going; their treatment must be explicit in the relevant domain.

## Epsilon and infinitesimals

Reserve `ε` as mathematical syntax without prematurely assigning it one universal meaning.

At least two distinct ideas must not be conflated:

1. a nilpotent/dual-number element satisfying `ε² = 0`;
2. an ordered nonstandard infinitesimal in the sense associated with Abraham Robinson, where for positive infinitesimal `ε`, `x + ε > x` and `x − ε < x`.

Those are different algebraic objects even though both are commonly written with epsilon.

## Indexed bit quantities and dependent facts

Fixed-width bit quantities should use a numeric index such as `Bits[n]`, not only unrelated names like `Bits8` and `Bits32`. Widths, bounds, and similar quantities should remain data available to type-level computation. The fuller refinement/dependent-type direction is isolated on `feature/dependent-refinement-types`.

## Laziness and deferred commitment

Several forms of deferral may be useful and should remain conceptually distinct:

- do not compute a value until demanded;
- do not allocate a representation until demanded;
- do not normalize a fraction until useful if benchmarks justify deferral;
- do not convert exact arithmetic to approximation until explicitly demanded;
- do not choose a machine representation until enough facts are known;
- do not materialize a Boolean object when a predicate can flow directly into control flow.

For example, a comparison used immediately by `if` may compile to compare-and-branch without ever allocating `True` or `False`. A Boolean stored or passed as data eventually needs a representation, but its mathematical type remains Boolean.

The guiding separation is:

```text
types                    describe mathematics
refinements/proofs       describe facts about values
explicit machine types   describe layouts when layout matters
compiler choices         are delayed while that preserves useful options
```
