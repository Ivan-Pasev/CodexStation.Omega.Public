# Omega UHP Slice 08 — CI Smoke and Evidence Intake Reconciliation

Date: 2026-11-05
Status: STACKED DRAFT / SYNTHETIC ONE-RUNNER SMOKE ONLY
Parent: canonical Slice 07 evidence-intake PR #36, commit 4e6594b5bc3f36f7b9ce6530d0d4698dc01d72d8
Parallel origin: PR #37 single-runner containment, commit a12f2e03a07ef0fa33be00b684a6f5dc3b016572

## Integration

PR #36 verifies provided event bytes against twelve negative-probe expectations but does not acquire them. PR #37 contributes a fixed CI Docker smoke using a synthetic public fixture. This new stacked branch combines the two without changing either prior branch or pretending they establish an independently operated two-host verifier.

The PR #37 workflow, fixed Go worker, shell runner, pure CI containment reviewer, 30 adversarial tests and runbook are reused by exact Git blob references. A separate pure bridge adds seventeen tests.

runtime08c/uhp_smoke_coverage.py:
  reconcile_ci_smoke(matrix, smoke_receipt)

This maps exactly N01, N03, N06 and N12 to POSSIBLY EXERCISED IN A SINGLE RUNNER, and records the other eight as NOT EXERCISED. All twelve remain EXTERNALLY UNQUALIFIED. N06 tests absence of a Docker socket, not comprehensive privilege escalation. N03 combines a fixed denied TCP attempt with claimed network=none but does not independently prove all egress blocked.

## Physical and authority limits

The GitHub-hosted disposable runner controls both Docker and inspection. It is a single trust/failure domain. It does not independently authenticate a machine, prove a protected observer signer, provide durable replay, run a real UHP model, exercise actual provider secrets or execute the full twelve-probe matrix.

Possible bridge result: PARTIAL_SINGLE_RUNNER_RESEARCH_ONLY. No input can yield a full qualification, dispatch authority, promotion, retry authorization or release. A HOLD smoke propagates no partial coverage.

The CI result must be verified from the actual workflow, not inferred from files. No production deploy or private corpus access. Omega 09M STABLE_WAIT remains HOLD.

## Next

Owner-authorized two-host disposable trial. Separately provision observer trust root, isolate principals and host failure domains, capture immutable events and source bytes, commit durable replay state and verify all negative probes independently.
