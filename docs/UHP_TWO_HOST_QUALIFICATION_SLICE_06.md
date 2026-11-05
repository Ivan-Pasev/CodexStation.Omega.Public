# Omega UHP Slice 06 — Two-Host Qualification Runbook and Safety Gate

Date: 2026-11-05
Status: OWNER MANUAL PILOT PREPARATION / NOT EXECUTED / DRAFT
Parent: canonical Slice 05 PR #33, b373ab47f5c52109a99b813f643127596ecdbcf9.
Source: original CodexStation integration; reuses legacy 09G/H host witnesses and UHP 01-05 contracts.
No dependency installation, actual host probing, model invocation or live action.

## Why this is not another cryptographic proof prototype

Existing cybernetic09h/run_host_witness.py has a classify_origin() branch
that assigns LIVE_HOST when a supplied attestation matches host ID, profile
digest, class and required fields. This is a claim-classification check.
Neither matching strings nor a signed self-report from the agent proves
physical host identity, observer independence or technical write confinement.
Slice 06 does NOT change the legacy 09H module or automatically upgrade
its historical statuses; it introduces a new stricter admission boundary.

## Two separated trust domains

EXTERNAL OBSERVER / EVIDENCE CONTROLLER:
- independently provisioned observer principal, host, key and evidence store;
- responsible for immutable pre/post source snapshots, nonce ledger, access logs,
  negative-test observations, source and artifact digests;
- receives no agent model instruction as authority; cannot self-approve release;
- if physically separate machines are unavailable, record the shared-failure
  domain and retain the independent-host qualification HOLD.

DISPOSABLE EXECUTOR / UHP HARNESS:
- owner-prepared isolated machine or VM with disposable data and no real secrets;
- exact source commit and byte digest pinned; no private corpus by default;
- read-only source mount, read-only root, non-root unprivileged UID,
  all Linux capabilities dropped, no-new-privileges, network disabled,
  no Docker socket, process/memory budgets enforced;
- no provider tokens or connected apps; use a predetermined local fixture
  rather than invoking a real LLM or worker for the initial negative probes.

INDEPENDENT GATE CONTROLLER:
- separate from both agent and observer; checks witness signatures against
  independently registered and rotated public keys, trust scope and revocation;
- checks durable replay journal transactionally, not with a JSON list;
- checks all required probes and source/artifact lineage;
- cannot use a caller-supplied HMAC key as an independent trust root.

## Fixed pilot acceptance matrix

Machine readable: ops/uhp06/qualification_matrix.json
C01..C12: required external controls.
N01..N12: write/network/credential/escape/tenant denial, artifact corruption,
replay, source pin, uncertain retry, unchanged source snapshot.
All controls and negative probes are mandatory, not optional.

runtime08c/uhp_host_qualification.py:
compile_host_pilot_plan(config, matrix) -> no-I/O plan.
assess_report(plan, matrix, report, legacy_host_witness=None) -> untrusted
report shape/claim consistency check. It never returns real PASS.
Only receipt class CLAIMS_COMPLETE_INDEPENDENT_PROOF_REQUIRED is possible
for complete self-supplied reports; independent proof remains HOLD.
Actual negative probe results and evidence must come from a separately
approved, externally controlled host workflow.

## Operator run sequence (NOT run by this PR)

A. Define the owner-approved, time-limited, disposable pilot scope, the
   two host identities and independent principals. Document asset ownership,
   legal permissions and the security officer responsible.
B. Use distinct rootless container runtimes or separate VMs on independent
   hosts; use exact signed/immutable image digests, not mutable tags.
C. Freeze a synthetic public fixture source commit and observer-acquired
   SHA-256 source manifest. Confirm agent cannot change the source.
D. From the owner-operated host, run the N01..N12 negative probes against
   only synthetic canaries. No real secrets or personal data.
E. Observer acquires evidence independently, with timestamped raw events,
   independent hashed snapshots, tool/permission traces and denial logs.
F. Verify external origin, key custody, revocation, immutable evidence,
   replay ledger and budget/timeout behavior before considering a scoped
   qualification closure. Retain all failure outputs for review.
G. Reconcile with inherited 09G/H/09I/09J and current UHP 01-05. Never
   infer release or canonical authority from successful local tests.

## Mandatory gate ledger

SOURCE_COMMIT_AND_BYTES: HOLD until independent source capture
OBSERVER_HOST_SEPARATION: HOLD until externally verified separate host
OBSERVER_KEY_CUSTODY: HOLD until independent registry and protected key
EXECUTOR_ISOLATION: HOLD until N01..N07 denial evidence
ARTIFACT_AND_REPLAY: HOLD until N08..N11 denial/retry evidence
NO_SOURCE_MUTATION: HOLD until N12 independent pre/post match
ACTUAL_UHP_TASK: NOT RUN
REAL_PROVIDER_COST_PRIVACY: NOT RUN
EXTERNAL_EFFECTS: NOT ATTESTED
RELEASE_AND_CANONICAL_PROMOTION: HOLD

Critical status boundary: implementation_tests_PASS does not certify any
of the above. Candidate is safe for repository CI and future operator
qualification planning only; 09M STABLE_WAIT remains unchanged.

## Verification

python -m unittest -v tests.test_uhp_host_qualification
python -m unittest discover -s tests -v

No default live execution command exists in the module. Do not install an
executor or send credentials based on this runbook alone.
