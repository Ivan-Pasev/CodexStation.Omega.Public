# Ω Tier-A Integration Harness Contract — v0.8d

## Purpose

This slice binds the pinned Tier-A source evidence from 08B to the constitutional reference runtime from 08C through a reproducible, fail-closed harness.

The pipeline is:

```text
pinned source commit/path
→ source-derived fixture
→ explicit normalization
→ 08C adapter
→ 0.8b constitutional ABI object
→ 08C reference runtime
→ correspondence observation
→ residual/loss record
```

## Non-collapse laws

- `SOURCE_FIXTURE != SOURCE_RUNTIME_EXECUTION`
- `NORMALIZATION != SEMANTIC_IDENTITY`
- `ADAPTER_PASS != FULL_SOURCE_INTEGRATION`
- `SOURCE_REPORTED_PASS != LOCALLY_REPRODUCED_PASS`
- `PURE_EFFECT_MODEL != EXTERNAL_EFFECT_CONFIRMATION`
- `TEST_PASS != FORMAL_PROOF`
- `IMPLEMENTATION_PASS != SCIENTIFIC_PASS`

## Required families

1. Digital.Fabrica.Core
2. DFPL / PRIMA
3. CodexStation.HighestOne
4. GILC.CodexStation
5. neural-lattice

## Required correspondence paths

The harness must exercise at least one source-derived vector per family and collectively cover:

- transition identity and predecessor binding;
- admission and semantic-deny behavior;
- predecessor-state authority;
- protected invariant fail-closed behavior;
- exact authorized-plan binding;
- external effect UNKNOWN_OUTCOME preservation;
- durable conflict representation;
- receipt before/after state binding;
- recovery success and quarantine boundaries.

## Evidence rule

A passing harness proves only that the checked source-derived fixtures, explicit normalization rules, 08C adapters and 08C runtime agree on the declared observations. It does not prove that every source repository executes under the shared runtime, that external effects occurred, or that formal/scientific claims are established.
