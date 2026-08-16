# Ithon recovered feature map

Canonical development repository: `isomorphisms/ithon`.

The dashed `isomorphisms/i-thon` repository is intentionally left untouched for later cleanup. Its recent history is upstream CPython rather than Ithon feature development.

`main` is also left untouched by this migration. Recovered work is separated so features can be tested, revised, and merged deliberately.

## Feature branches

### `feature/unicode-syntax`

Names the already implemented parser/tokenizer slice in the canonical tree and documents:

- `←` left assignment;
- `→` right assignment / rightward flow;
- `×`, `•`, `·` multiplication;
- `÷` division;
- `λ` and `ƒ` anonymous functions;
- Unicode arithmetic operators do not replace `*` in unpacking/varargs syntax.

The executable syntax regressions remain in `Lib/test/test_ithon_syntax.py`.

### `feature/mandatory-static-typing`

Contains a mandatory static checker, its core regression suite, Unicode/type-system interaction tests, and the type-system contract.

The contract includes no implicit `Any`, stable inferred assignment types, typed function parameters/results, contextual `Callable` typing for lambdas, explicit typed foreign-library boundaries, and whole-module checking before execution.

### `feature/launcher`

Contains the smallest executable repo-local `./ithon` wrapper around the completed native build.

### `feature/pi-source-files`

Uses the mandatory-static-typing work as a dependency and adds the strict runner/importer and executable launcher.

Current source boundary:

- `.pi` = Ithon;
- `.py` = Python.

The runner loads `.pi` modules/packages, leaves `.py` to ordinary Python import machinery, rejects a `.py` file passed as an Ithon program, and checks an Ithon module before executing it.

This supersedes earlier experiments using `.ithon` or keeping Ithon-owned source in `.py` files.

### `feature/exact-mathematics`

Records the recovered mathematical-semantics direction:

- exact rational division;
- Macaulay2 semantic debt/provenance policy;
- rings, fraction fields, and polynomial rings;
- square roots enlarging into the complex domain;
- `∈` and `∋` membership spellings;
- explicit treatment of infinity and indeterminate expressions;
- distinct meanings for dual-number versus nonstandard-analysis epsilon;
- delayed representation and exactness-preserving compilation.

### `feature/dependent-refinement-types`

Separates richer type-system work from the first mandatory checker:

- `Bits[n]` and numeric widths;
- bounds and sizes as type-level numbers;
- simultaneous refinement facts about values;
- source mathematical type separated from machine representation.

### `feature/dogfood`

Records the project-wide dogfooding contract. IRK and Grease are existing Ithon integration targets; new Ithon-owned source should use `.pi` and `#!/usr/bin/env ithon`. Bootstrap fallbacks must be explicit and must not masquerade as Ithon execution.

## Superseded directions preserved by this map

The following earlier choices are not the current direction:

- treating Ithon primarily as an upstream-friendly CPython patch series;
- using `.ithon` as the Ithon extension;
- keeping Ithon-owned source in `.py` and selecting the language only by interpreter.

Python remains valuable as implementation substrate, compatibility source, and foreign-library ecosystem. It is not the audience whose acceptance governs Ithon's design.
