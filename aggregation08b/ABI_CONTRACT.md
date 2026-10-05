# CodexStation Ω — Tier-A Pinned Constitutional ABI v0.8b

Status: WORKING EXECUTABLE ABI CANDIDATE / NOT RELEASED  
Authority delta: NONE

## Purpose

Bind the first five Tier-A source repositories to exact commits and expose the smallest shared constitutional interface that can connect deterministic state, law, authority, continuity, conflict, receipts and recovery without forcing the source projects into one implementation.

Pinned sources:

- Digital.Fabrica.Core
- DFPL / PRIMA
- CodexStation.HighestOne
- GILC.CodexStation
- Neural Lattice

The ABI is an interoperability layer.

```text
SOURCE PROJECT != ABI
ABI != SOURCE AUTHORITY
ADAPTER != SEMANTIC IDENTITY
ADAPTER != AUTHORITY PROMOTION
```

## Constitutional compute path

```text
CanonicalState
  -> CandidateTransition
  -> semantic DecisionVector
  -> invariant evaluation
  -> authorization
  -> effect execution
  -> Receipt
  -> Conflict / Closure
  -> admitted successor state
  -> RecoveryEvidence / replay
```

The phases MUST remain separable.

```text
SEMANTIC_DECISION != AUTHORIZATION_DECISION
AUTHORIZATION_DECISION != EXECUTION_OUTCOME
EXECUTION_OUTCOME != CLOSURE_DECISION
```

## ABI primitives

1. CanonicalDigest
2. Principal
3. AuthorityGrant
4. CanonicalState
5. CandidateTransition
6. InvariantEvaluation
7. DecisionVector
8. Event
9. Receipt
10. Conflict
11. RecoveryEvidence

## Source mappings

### Digital.Fabrica.Core

- `TransitionProposal -> CandidateTransition`
- `AdmissionDecision -> DecisionVector.admission`
- `InvariantEvaluation -> InvariantEvaluation`
- `FabricEvent -> Event`
- `WitnessRecord -> Receipt`

Strongest reusable pattern: fail-closed transition admission over current-state identity + authority + invariant + evidence + policy checks.

### DFPL / PRIMA

- `LawIRBody -> policy/law binding`
- `AuthenticatedPrincipal -> Principal`
- `AuthorizationArtifact -> authority/authorization projection`
- `GatewayRequest + OutcomeReceipt -> transition/execution/receipt projection`

Strongest reusable pattern: semantic verdict, runtime authorization and effect outcome are distinct constitutional phases.

### CodexStation.HighestOne

- `State -> CanonicalState`
- `Grant -> AuthorityGrant`
- `Transition -> CandidateTransition`
- `Receipt -> Receipt`
- `RecoveryEvidence -> RecoveryEvidence`

Strongest reusable pattern: predecessor-state authorization plus non-governance authority preservation and fail-closed recovery quarantine.

### GILC.CodexStation

- `Authority -> authority-level profile`
- `EffectIntent -> CandidateTransition projection`
- `EffectReceipt -> Receipt`
- `Checkpoint -> CanonicalState + recovery/migration projection`
- `MemoryRecord -> state payload/provenance projection`

Strongest reusable pattern: entity/station root separation plus receipted effects and migration integrity.

### Neural Lattice

- `NL-1 State Cell -> CanonicalState`
- `Transition Receipt -> Receipt`
- `Conflict Object -> Conflict`
- `Closure Policy -> closure/gate projection`

Strongest reusable pattern: provenance-bearing state cells, explicit conflict and reopenable closure.

## Shared laws extracted from the five source families

```text
AUTHORIZATION_EVALUATED_ON_PREDECESSOR_STATE
NO_SUCCESSOR_AUTHORITY_BOOTSTRAP
NON_GOVERNANCE_TRANSITION_CANNOT_IMPLICITLY_ESCALATE_AUTHORITY
PARENT_STATE_IDENTITY_MUST_MATCH_CURRENT_STATE
PROTECTED_INVARIANTS_FAIL_CLOSED
EXACT_AUTHORIZED_PLAN_BINDING_REQUIRED
UNSUPPORTED_EFFECTS_ARE_REJECTED_NOT_APPROXIMATED
UNKNOWN_OUTCOME_IS_PRESERVED_AS_UNKNOWN
CONFLICT_IS_DURABLE_STATE
RECOVERY_WITH_UNVERIFIED_OBJECTS_OR_RECEIPT_QUARANTINES
```

## Engineering interpretation

This ABI is deliberately narrower than any one source project.

That is a feature.

A source adapter MUST state:
- direct fields;
- normalized fields;
- split/merged fields;
- omitted fields;
- loss;
- unresolved semantics.

A provider/runtime MUST NOT infer missing fields.

## First use

The ABI is the substrate for the next executable reference slice:

```text
SOURCE MOUNT
-> ABI ADAPTER
-> CANONICAL STATE
-> CANDIDATE TRANSITION
-> LAW / INVARIANT / AUTHORITY GATES
-> ISOLATED EFFECT
-> RECEIPT
-> EVENT FOLD
-> CONFLICT/CLOSURE
-> RECOVERY / REPLAY
```

This is the bridge from accumulated project knowledge to a working sovereign digital runtime.

## Open boundaries

- source repository CI is not re-run by this slice;
- source project maturity remains source-scoped;
- formal proof status remains lineage-specific;
- integration of all five implementations is not yet claimed;
- live host conformance remains OPEN;
- license/IP review remains OPEN;
- release eligibility remains false.
