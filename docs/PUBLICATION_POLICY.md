# Public Publication Policy

## Boundary

A private object is not public merely because it is useful. A public object is not stronger merely because it is published.

```text
SOURCE
-> LINEAGE
-> SECRET/PII CHECK
-> LICENSE/IP CHECK
-> CLAIM/EVIDENCE CLASSIFICATION
-> AUTHORITY CEILING
-> PROVENANCE
-> DEDUP/SUPERSESSION
-> PUBLICATION WITNESS
-> COMMIT
```

## Gate semantics

- `OPEN`: evidence missing or human decision required.
- `PASS_CANDIDATE_BOOTSTRAP`: the bootstrap validator found no blocking structural issue; not a full release approval.
- `PASS`: an explicitly scoped gate was discharged by admissible evidence.
- `FAIL`: publication blocked.
- `HOLD`: publication paused pending a named dependency.

## Claim classes

Public material SHOULD distinguish:
`DEFINITION`, `DERIVED_LAW`, `THEOREM_TARGET`, `FORMAL_THEOREM`,
`FINITE_MACHINE_EVIDENCE`, `EMPIRICAL_EVIDENCE`, `ENGINEERING_PROPOSAL`,
and `EXTERNAL_PUBLIC_ANCHOR`.

## Licensing

The repository currently has no project license. That is deliberate.

Until the license gate closes:
- do not copy substantial third-party text;
- prefer original synthesis and links to public sources;
- keep code/documentation licensing decisions explicit;
- do not interpret public visibility as permission to reuse everything under arbitrary terms.

## Distribution

Platform builds are generated views.

```text
PUBLIC_CANON -> CHATGPT_DIST
PUBLIC_CANON -> GEMINI_DIST
```

A provider-specific build may change packaging, indexing or sharding. It may not silently alter semantics or claim status.

## Deduplication and supersession scope

The release deduplication gate is discharged only for **machine-addressable public declarations** enumerated by `cybernetic09n/DEDUP_SCOPE.json`. The audit checks canonical identifier uniqueness, identical normalized payloads under different identifiers, explicit supersession/alias integrity, and supersession cycles.

A scoped object-level `PASS` does **not** claim semantic uniqueness of free-form prose, third-party source bodies, cross-repository concepts, or same-labeled objects in distinct lineages.

```text
SCOPED_DEDUP_PASS != GLOBAL_SEMANTIC_UNIQUENESS
SAME_LABEL != SAME_LINEAGE
SUPERSESSION != DELETION
```
