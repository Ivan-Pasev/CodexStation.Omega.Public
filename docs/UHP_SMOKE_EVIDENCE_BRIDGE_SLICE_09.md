# Omega UHP Slice 09 — Evidence Intake × Single-Runner Smoke Coverage

Date: 2026-11-05
Status: STACKED DRAFT / SYNTHETIC ONE-RUNNER SMOKE ONLY
Parent: canonical Slice 08 disposable single-runner smoke PR #38, commit 887bd19edea030a75750a2f6eb843b8ebad7b4d8
Lineage: Slice 07 evidence-intake PR #36; Slice 08 CI Docker smoke PR #38; parallel PR #37 preserved as original smoke research

## Integration

PR #36 verifies provided event bytes against twelve negative-probe expectations but does not acquire them. PR #38 contributes a fixed CI Docker smoke using a synthetic public fixture. This child adds only a bounded static partial-coverage bridge, without changing the established smoke or evidence-intake code, and does not pretend to establish an independently operated two-host verifier.

The existing PR #38 workflow, fixed Go worker, shell runner, pure CI containment reviewer, thirty adversarial tests and runbook are inherited from its parent. This change adds a pure bridge with seventeen regression tests; no smoke runner changes are needed.

runtime08c/uhp_smoke_coverage.py:
  reconcile_ci_smoke(matrix, smoke_receipt)

This maps exactly N01, N03, N06 and N12 to POSSIBLY EXERCISED IN A SINGLE RUNNER, and records the other eight as NOT EXERCISED. All twelve remain EXTERNALLY UNQUALIFIED. N06 tests absence of a Docker socket, not comprehensive privilege escalation. N03 combines a fixed denied TCP attempt with claimed network=none but does not independently prove all egress blocked.

## Physical and authority limits

The GitHub-hosted disposable runner controls both Docker and inspection. It is a single trust/failure domain. It does not independently authenticate a machine, prove a protected observer signer, provide durable replay, run a real UHP model, exercise actual provider secrets or execute the full twelve-probe matrix.

Possible bridge result: PARTIAL_SINGLE_RUNNER_RESEARCH_ONLY. No input can yield a full qualification, dispatch authority, promotion, retry authorization or release. A HOLD smoke propagates no partial coverage.

The CI result must be verified from the actual workflow, not inferred from files. No production deploy or private corpus access. Omega 09M STABLE_WAIT remains HOLD.

## Next

Owner-authorized two-host disposable trial. Separately provision observer trust root, isolate principals and host failure domains, capture immutable events and source bytes, commit durable replay state and verify all negative probes independently.
