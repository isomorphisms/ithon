# Ithon dogfooding

Ithon is not only a syntax experiment. The surrounding projects should use it so failures appear in real programs rather than only in isolated parser tests.

## Canonical dependency

Projects that use Ithon should use the canonical repository:

```text
isomorphisms/ithon
```

The dashed `i-thon` repository is not the language-development source.

## Source and entrypoints

New Ithon-owned source uses `.pi`. Ordinary Python remains `.py`.

Executable Ithon programs should be able to use:

```text
#!/usr/bin/env ithon
```

A repository-local build may invoke its checked-out Ithon executable directly when that makes the dependency explicit.

## Projects already used as dogfood targets

IRK and Grease have both been used to exercise Ithon syntax. Earlier experimental patches converted real code to `←`, `→`, `×`, and `λ`/`ƒ`, and changed entrypoints to run through Ithon.

Those older experiments sometimes kept `.py` filenames or invoked the built CPython-named binary directly. The current direction supersedes that naming: Ithon-owned source should migrate to `.pi` and execute as Ithon; `.py` is foreign Python.

## Build policy

When practical, Ithon's dependent projects should build, run, or test with Ithon rather than silently using stock Python.

Bootstrap fallbacks may exist where required, but they must be visibly separated from the intended dogfood/self-hosting path. A fallback must not make a test appear to exercise Ithon when it actually exercised ordinary Python.

Representative integration checks should include real programs using the Ithon syntax and type rules, not only tokenizer or parser artifacts.
