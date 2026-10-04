# OMEGA SKILL SPINDLE — Public Genesis v0.1

Status: PUBLICATION-STAGING

A skill is a reusable typed method. It is not an agent identity, tool capability, permission grant or truth source.

## Skill object

```yaml
SKILL:
  skill_uri: ""
  name: ""
  version: ""
  class: ""
  status: ""
  lineage: ""
  intent: ""
  accepts: []
  preconditions: []
  method: []
  emits: []
  guards: []
  source_provenance: []
  qualification_evidence: []
  required_capabilities: []
  host_bindings: []
  authority_ceiling: ""
  freshness: ""
  tests_receipts: []
  supersedes: []
  retrieval_tags: []
  context_cost: ""
  failure_modes: []
```

## Public spindle seed

### cs.skill::source-audit::v0.1
Intent: classify source lineage, authority claims, conflicts, version and evidence boundary before integration.

### cs.skill::formalize-claim::v0.1
Intent: convert a prose claim into definitions, assumptions, scope, dependencies, obligations, proof status and counterexample targets.

### cs.skill::adversarial-review::v0.1
Intent: challenge identity collapse, authority inflation, unsupported claims, stale state, hidden-memory dependence and missing evidence.

### cs.skill::repository-mutation::v0.1
Intent: make bounded repository changes after reading current state; preserve branch/SHA lineage; validate and issue receipts.

### cs.skill::publication-filter::v0.1
Intent: determine whether a private candidate is admissible for public release under secret, IP, claim-status, provenance and duplication gates.

### cs.skill::migration-witness::v0.1
Intent: record source/target substrate, transferred state, hashes, preserved invariants, residual loss, replay result and authority delta.

## Routing law

Before applying a skill ask:
1. does the mission match intent?
2. do preconditions hold?
3. is the skill qualified for this scope?
4. are required capabilities observed now?
5. is execution authorized?
6. what evidence ceiling applies?
7. what receipt demonstrates completion?

Unknown hard answers fail closed or route to a non-destructive fallback.
