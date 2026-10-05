# Ω Tier-A Independent Reproduction Contract — v0.8e

## Mission

08E raises the evidence class only where a pinned Tier-A source can actually be executed without violating source authority, repository privacy, or toolchain boundaries.

The admissible chain is:

```text
08D source-bound fixture/correspondence
→ exact pinned source identity
→ native toolchain discovery
→ native execution where admissible
→ execution receipt
→ comparison to 08D scope
→ evidence-class promotion or explicit HOLD
```

## Evidence classes

**INDEPENDENT_CROSS_REPO_NATIVE_EXECUTION** means Ω Public CI checks out an exact public source commit and executes that source repository's native test command from outside the source repository.

**SOURCE_NATIVE_EXACT_COMMIT_CI** means the source repository itself has a successful native CI execution on the exact pinned commit. This is stronger than static source inspection but is not independent reproduction.

**SOURCE_NATIVE_LINEAGE_APPLICABLE_CI** means a successful native run exists on an ancestor and the relevant executable/formal tree is verified unchanged through the pinned commit. It is evidence continuity, not new execution.

**PARTIAL_SOURCE_NATIVE_REPRODUCTION** means an executable native surface is reproduced, but it does not cover the exact semantic slice used by 08D.

**HOLD_PRIVATE_OR_MISSING_REPRO_SURFACE** is neither PASS nor FAIL. It means the present authority/tool boundary does not permit a truthful reproduction.

## Source decisions

- Digital.Fabrica.Core: HOLD. Private; no exact-pin native workflow.
- DFPL / PRIMA: independently execute the public Encoder B sentinel, but keep PRIMA authorization/effect semantics on HOLD because the pinned public source describes a private Rust runtime model rather than containing that executable harness.
- HighestOne: retain successful Lean machine-check evidence from run 33790374960 as lineage-applicable source-native evidence only; do not call it independent reproduction.
- GILC.CodexStation: independently reproduce the exact public pin under Python 3.11, 3.12 and 3.13.
- neural-lattice: preserve exact-commit successful native run 33970167198 as source-native evidence only; private source is not copied into Ω Public CI.

## Non-collapse laws

- `SOURCE_REPORTED_PASS != LOCALLY_REPRODUCED_PASS`
- `SOURCE_NATIVE_RUN != INDEPENDENT_CROSS_REPO_REPRODUCTION`
- `UNCHANGED_RELEVANT_TREE != NEW_EXECUTION`
- `PARTIAL_NATIVE_TEST != FULL_SEMANTIC_CORRESPONDENCE`
- `HOLD != FAIL`
- `REPRODUCTION_PASS != RELEASE`

08E may close as a bounded reproduction slice with explicit HOLDs. It may not silently promote held private or missing-runtime families.
