# OMEGA CRYSTAL — Public Genesis v0.1

Status: PUBLICATION-STAGING / SEMANTIC KERNEL

The full private Crystal is not published here. This file establishes the public semantic kernel into which publication-admissible material can be metabolized.

## 1. Universal object envelope

```yaml
UOBJECT:
  id: ""
  kind: ""
  namespace: ""
  version: ""
  state: ""
  scope: ""
  boundary: ""
  relations: []
  constraints: []
  invariants: []
  assumptions: []
  evidence: []
  authority: {}
  uncertainty: {}
  failure_modes: []
  provenance: {}
```

## 2. Canonical relation vocabulary

```text
DEPENDS_ON
USES
ASSUMES
IMPLEMENTS
PROVES
CHECKS
SUPPORTS
CONTRADICTS
REFINES
GENERALIZES
SPECIALIZES
VALIDATES
INVALIDATES
BINDS
SUPERSEDES
DERIVES_FROM
REPRESENTS
CONSTRAINS
TESTS
MEASURES
REPRODUCES
REPLICATES
BRIDGES_TO
BLOCKS
DISCHARGES
OBSERVED_BY
CONTROLLED_BY
ESTIMATED_BY
ASSOCIATED_WITH
```

A relation is typed and scoped. A convenient word such as “equivalent” never replaces a declared relation class.

## 3. Anti-collapse registry

```text
OBJECT != DESCRIPTION_OF_OBJECT
MODEL != REALITY
REPRESENTATION != REFERENT
NAME_IDENTITY != TYPE_IDENTITY
DATA != INFORMATION != KNOWLEDGE
OBSERVATION != INTERPRETATION != EXPLANATION
CORRELATION != CAUSATION
VERIFICATION != VALIDATION
PRECISION != ACCURACY
ROBUSTNESS != RESILIENCE
SECURITY != SAFETY
PUBLICATION != REPLICATION
SOURCE != AUTHORITY
CLAIM != EVIDENCE
FORMAL_PROOF != EMPIRICAL_CONFIRMATION
SIMULATION != EXPERIMENT
IMPLEMENTATION_PASS != SCIENTIFIC_PASS
SAME_LABEL != SAME_LINEAGE
```

## 4. Status vector

No single maturity scalar is constitutional.

```yaml
STATUS_VECTOR:
  formal: OPEN | SPECIFIED | PARTIAL | CHECKED | INDEPENDENT_CHECKED
  empirical: NONE | OBSERVED | SUPPORTED | REPLICATED | CONTESTED
  execution: NOT_EXECUTED | PARTIAL | PASS | FAIL
  reproduction: NONE | LOCAL | INDEPENDENT
  implementation: SPECIFIED | IMPLEMENTED | TESTED | QUALIFIED | DEPLOYED
  publication: PRIVATE | DRAFT | RELEASED | ARCHIVED
  canon: EXPLORATORY | AUTHORIAL | CANON_CANDIDATE | CANON | SUPERSEDED
```

## 5. Evidence discipline

Evidence entries carry type, environment, method, scope and a `does_not_establish` boundary.

Unknown is not upgraded to PASS.

## 6. Canon admission

Admissible outcomes:

```text
ADMIT
SUPERSEDE
QUARANTINE
CONTEST
REJECT
HOLD
```

Admission is a governed state transition, not a synonym for “the model liked it.”

## 7. Research closure

Valid research outcomes include:
`CLOSED_PROVED`, `CLOSED_REFUTED`, `CLOSED_EMPIRICALLY_SUPPORTED`,
`CLOSED_NO_GO`, `HOLD_INSUFFICIENT_EVIDENCE`, `HOLD_CONTRADICTION`,
`HOLD_MISSING_BRIDGE`, `HOLD_RESOURCE_LIMIT`, `HOLD_CAPABILITY_LIMIT`,
and `SPLIT_COMPETING_MODELS`.

Negative results are retained as state.
