# CodexStation Ω Public — ChatGPT / Codex Reference Runtime View v0.8c

Status: REFERENCE IMPLEMENTATION CANDIDATE / NOT RELEASED  
Previous composite semantic fingerprint: `cf9bc1de879c91756640cc145538324787646868811fa8ca9007e363b11c7de3`  
Authority delta: NONE

## Advance

The v0.8b Constitutional ABI now has a provider-independent deterministic reference runtime candidate.

```text
MISSION HOLOTOPE
-> ARCHETONIC PLATE
-> CandidateTransition
-> semantic / invariant / predecessor-authority / plan-binding gates
-> pure reducer OR isolated effect interface
-> Receipt + Event
-> closure
-> successor state
-> replay / recovery
```

Local pure operations:
`SET`, `DELETE`, `ASSERT`, governance-only `GRANT`.

`EFFECT` is not silently simulated. Without an admissible executor/witness it resolves to `UNKNOWN_OUTCOME`, `HOLD`, and no successor state.

## Permanent runtime laws

```text
PREDECESSOR_AUTHORITY_ONLY
NO_SUCCESSOR_AUTHORITY_BOOTSTRAP
STALE_PARENT -> HOLD
UNRESOLVED_PROTECTED_INVARIANT -> HOLD
EXACT_AUTHORIZED_PLAN_BINDING_REQUIRED
UNKNOWN_EFFECT_OUTCOME -> HOLD
CONFLICT_IS_DURABLE_STATE
RECOVERY_MISMATCH -> QUARANTINE
```

Five source-family adapters remain explicit and potentially lossy:
Digital.Fabrica.Core, DFPL/PRIMA, HighestOne, GILC.CodexStation, Neural Lattice.

The bundled runtime source is reference code. Host execution must be observed separately.

```text
REFERENCE_IMPLEMENTATION != PRODUCTION_RUNTIME
ADAPTER_PASS != FULL_SOURCE_INTEGRATION
TEST_PASS != FORMAL_PROOF
LIVE_PROVIDER_CONFORMANCE = OPEN
```
