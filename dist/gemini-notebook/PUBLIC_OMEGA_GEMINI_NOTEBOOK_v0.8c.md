# CodexStation Ω Public — Gemini Notebook Reference Runtime View v0.8c

Status: REFERENCE IMPLEMENTATION CANDIDATE / NOT RELEASED  
Previous composite semantic fingerprint: `cf9bc1de879c91756640cc145538324787646868811fa8ca9007e363b11c7de3`  
Authority delta: NONE

The Notebook remains a bounded research/reasoning cell. It may inspect the runtime contract and source code, derive transitions and receipts, and reason about replay/recovery, but Notebook attachment alone does not establish execution.

## Runtime path

```text
PROJECT / MISSION CONTEXT
-> HOLOTOPE
-> ARCHETONIC PLATE
-> CandidateTransition
-> semantic / invariant / predecessor-authority / plan-binding gates
-> pure local reduction OR isolated effect interface
-> Receipt / Event
-> closure
-> replay / recovery
```

## Fail-closed semantics

```text
STALE_PARENT -> HOLD
MISSING_INVARIANT -> HOLD
INSUFFICIENT_PREDECESSOR_AUTHORITY -> HOLD
NON_GOVERNANCE_AUTHORITY_ESCALATION -> HOLD
UNKNOWN_EFFECT_OUTCOME -> HOLD
RECOVERY_MISMATCH -> QUARANTINE
```

Use `RUNTIME_CONTRACT.md` as the primary Notebook source. Use `_runtime/` and `_machine/` when exact implementation or ABI details are required.

```text
NOTEBOOK != STATION
NOTEBOOK_REASONING != RUNTIME_EXECUTION
REFERENCE_IMPLEMENTATION != PRODUCTION_RUNTIME
ADAPTER_PASS != FULL_SOURCE_INTEGRATION
LIVE_NOTEBOOK_CONFORMANCE = OPEN
```
