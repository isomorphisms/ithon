# Ithon dependent and refinement typing

Mandatory ordinary static typing is only the first pass. Ithon should be able to retain and use mathematical facts about values rather than forcing every useful fact into a separate nominal runtime type.

A value may simultaneously have facts such as:

- `7` is an integer;
- `7` is nonnegative;
- `7` is odd;
- `7` is nonzero;
- `7` fits in 3 unsigned bits;
- `7` fits in 8 bits;
- `7` is prime.

These are refinement/dependent facts available to checking and optimization. They need not imply seven unrelated boxed runtime types.

## Indexed quantities

Fixed-width bit quantities should be indexed by a number:

```text
Bits[n]
```

rather than being defined only as an unrelated family such as `Bits8`, `Bits16`, `Bits32`.

Aliases may still exist:

```text
Byte   = Bits[8]
Word32 = Bits[32]
Word64 = Bits[64]
```

Keeping width as data permits type-level relationships such as:

```text
concatenate : Bits[m] × Bits[n] -> Bits[m + n]
```

Array bounds, byte counts, shift counts, vector lengths, and similar quantities should likewise remain numbers available to computation and proof when practical.

## Mathematical type versus machine representation

Source-level mathematical types and machine layouts are separate questions.

The compiler may prove that an exact integer, rational, index, or other value fits in a particular representation and choose that representation without changing what the source-level value mathematically is.

Dyadic rationals are a useful example: a rational whose reduced denominator is a power of two has a finite binary expansion. That fact can guide representation without changing the value's source-level mathematical type.

The intended separation is:

```text
types                         describe mathematical objects
refinements and proofs        describe facts about values
explicit machine types        describe layouts when layout matters
compiler representation       is delayed until enough facts are known
```

This branch is downstream of the mandatory-static-typing direction but deliberately separate from the first static checker so the basic language can become type-safe before the richer proof system is complete.
