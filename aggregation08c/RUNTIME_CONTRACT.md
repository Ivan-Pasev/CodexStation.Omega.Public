# CodexStation Ω — Constitutional Reference Runtime v0.8c

Status: REFERENCE IMPLEMENTATION CANDIDATE / NOT RELEASED  
Authority delta: NONE

## Purpose

Turn the v0.8b Constitutional ABI from a cross-project contract into a small executable provider-independent runtime.

This runtime is intentionally pure and deterministic by default.

It is not a production effect executor.

## Runtime path

```text
CanonicalState
-> CandidateTransition
-> semantic decision
-> protected invariant gate
-> predecessor-state authority gate
-> exact plan binding
-> deterministic local reducer OR isolated effect interface
-> Receipt
-> Event
-> closure
-> successor CanonicalState
-> replay / recovery check
```

If an external effect has no admissible executor/witness:

```text
EFFECT
-> UNKNOWN_OUTCOME
-> HOLD
-> NO SUCCESSOR STATE
```

Unknown is not converted to success or failure.

## Local deterministic operations

- SET
- DELETE
- ASSERT
- GRANT — governance transitions only
- EFFECT — requires explicit executor; otherwise UNKNOWN_OUTCOME

## Authority

Authorization is evaluated only against predecessor-state grants.

A non-governance transition cannot use its own proposed successor grants to authorize itself.

## Invariants

Every protected invariant must have an explicit PASS record.

Missing or UNRESOLVED protected invariants fail closed to HOLD.

## Receipts

Every attempted transition emits a receipt containing:
- subject transition;
- before digest;
- after digest when admitted and applied;
- authority refs;
- invariant results;
- evidence refs;
- decision vector;
- execution outcome.

## Replay

A sequence of pure transitions can be replayed deterministically from an initial state.

Replay equality is implementation evidence only.

## Recovery

Recovery checks:
- source and target state digests;
- receipt before binding;
- receipt after binding;
- PASS outcome.

Failure quarantines instead of silently recovering.

## Archetonic Plate bridge

A mission Archetonic Plate can compile to CandidateTransition through an explicit interface.

This is the first step from context-only Plates toward executable Plates.

```text
MISSION HOLOTOPE
-> ARCHETONIC PLATE
-> CandidateTransition
-> gates
-> execution
-> receipt
-> feedback / lattice admission
```

## Source adapters

The runtime exposes five adapter profiles:
- DIGITAL_FABRICA_CORE
- DFPL_PRIMA
- HIGHESTONE
- GILC_CODEXSTATION
- NEURAL_LATTICE

Adapters remain explicit and lossy where source systems differ.

## Boundary

```text
REFERENCE_IMPLEMENTATION != PRODUCTION_RUNTIME
TEST_PASS != FORMAL_PROOF
PURE_EFFECT_MODEL != EXTERNAL_EFFECT_CONFIRMATION
ADAPTER_PASS != FULL_SOURCE_INTEGRATION
```
