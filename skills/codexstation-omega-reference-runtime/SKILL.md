---
name: codexstation-omega-reference-runtime
description: Apply or inspect the deterministic public Omega constitutional reference runtime over the v0.8b ABI while preserving predecessor-state authority, fail-closed invariants, unknown effect outcomes, durable conflicts, replay and recovery boundaries.
---

# CodexStation Ω Constitutional Reference Runtime

Use this skill when a mission or project delta should be compiled to a bounded `CandidateTransition`, evaluated under the public Constitutional ABI, replayed, or recovery-checked.

## Runtime law

```text
CanonicalState
-> CandidateTransition
-> semantic decision
-> protected invariant gate
-> predecessor-state authority gate
-> exact plan binding
-> pure local reducer OR isolated effect interface
-> Receipt
-> Event
-> closure
-> successor CanonicalState
-> replay / recovery check
```

## Fail-closed rules

- stale/foreign parent -> HOLD;
- missing or unresolved protected invariant -> HOLD;
- insufficient predecessor-state authority -> HOLD;
- non-governance authority escalation -> HOLD;
- plan mutation after authorization -> HOLD;
- external effect without an admissible executor/witness -> UNKNOWN_OUTCOME + HOLD + no successor;
- receipt/state mismatch during recovery -> QUARANTINE.

## Source adapters

The reference runtime contains explicit adapters for:
- DIGITAL_FABRICA_CORE
- DFPL_PRIMA
- HIGHESTONE
- GILC_CODEXSTATION
- NEURAL_LATTICE

Adapter loss is part of the result. `ADAPTER_PASS != FULL_SOURCE_INTEGRATION`.

## Host capability boundary

The bundled Python files are reference implementation artifacts.

```text
SKILL != HOST_CAPABILITY
SOURCE_PRESENT != CODE_EXECUTED
REFERENCE_IMPLEMENTATION != PRODUCTION_RUNTIME
PURE_EFFECT_MODEL != EXTERNAL_EFFECT_CONFIRMATION
TEST_PASS != FORMAL_PROOF
```

If Python execution is actually available and authorized, run the validator or unit tests. Otherwise reason from the contract and preserve execution status as NOT_EXECUTED.

## References

- `references/RUNTIME_CONTRACT.md`
- `references/RUNTIME_PROFILE.json`
- `references/REFERENCE_SCENARIOS.json`
- `references/CONSTITUTIONAL_ABI.json`
- `references/SOURCE_BINDINGS.json`
- `scripts/runtime.py`
- `scripts/adapters.py`
