# CodexStation Ω · UHP Slice 07 — Captured Probe Evidence Intake

Date: 2026-11-05
Status: Draft source candidate; pure, no-I/O intake; NO actual host trial.
Exact parent: Slice 06 PR #35, 0ebf3e57a2d57f7bdcc80741782f2d402f1e3931.
Provenance: original CodexStation implementation; no external source imported.

## Purpose

Turn the C01–C12 / N01–N12 qualification protocol into a concrete, bounded
evidence intake interface. An observer-controlled workflow can *later* produce
per-probe JSON event bytes and independent pre/post source bytes. This slice
only checks data that a caller supplies. It is NOT an independent collector.

## API

runtime08c/uhp_capture_intake.py:
evaluate_capture_intake(plan, matrix, report, capture, evidence_bytes,
                        before_bytes, after_bytes)

Inputs:
- The exact Slice 06 immutable plan and 12-probe matrix.
- A Slice 06 untrusted host-pilot report, consistent with the plan.
- A capture claim bound to plan ID, claimed observer/executor hosts and
  principals, collector-session ID and the two source snapshot digests.
- Exactly one bounded raw JSON *byte* event per expected probe. Each event
  has a probe ID/outcome, plan ID, host/principal bindings, sequence, epoch,
  nonce and collector session ID. Strict JSON parsing refuses duplicate keys.
- Exact before/after bytes; inherited Slice 04 snapshot_manifest digests
  must match the declared capture digests. The source-before digest is bound
  to the planned immutable source hash; read-only changes are HOLD.

Checks:
- No missing/orphaned event files, duplicate probes, unsafe paths,
  malformed JSON, unbounded event payload, or hidden authorization fields.
- The claimed event outcome must equal the corresponding qualification
  matrix and the Slice 06 report; ALLOWED instead of DENIED -> HOLD.
- Sequence, nonce, timestamps and distinct claimed host/principal identities
  must be internally consistent. None is a durable replay/clock proof.

Possible outcomes:
- CAPTURE_BYTES_CONSISTENT_INDEPENDENCE_HOLD: all *supplied* bytes and
  relationships are internally consistent. NOT independently attested.
- HOLD: inconsistent probe, source change, missing independent evidence or
  failed prior qualification.
- UHPContractError: untrusted malformed structure; future callers must
  handle as HOLD and must not retry or dispatch.

Outputs include only digests, bounded reasons and scope identifiers, not
raw artifact/event payloads or credentials. The function never opens a file,
executes a command, starts a sandbox, accesses a network or changes a state.

## Two-host operational acquisition design (future, not performed here)

Observer host:
1. Independently acquire immutable-source pre/post byte snapshots and the
   designated raw events from a controlled observation channel.
2. Capture denial traces from every N01–N12 probe (synthetic target only).
3. Retain signed key-custody and independent host-origin evidence externally.
4. Commit each nonce, event identity and source hash to a durable journal
   transactionally. Caller supplied timestamps cannot close this gate.

Executor host:
1. Run only after owner signs off on a disposable, no-provider, no-credential
   scope, distinct principal/host, read-only source mount and no network.
2. Perform exact probe list, recording any ALLOWED, UNKNOWN or error as a
   failure; never silently reinterpret missing evidence as DENIED.
3. Do not send source documents, credentials, personal data or synthetic
   secrets to any LLM or external tool.

Independent verification:
1. First verify external observer host identity, hardware/VM provenance,
   protected asymmetric key chain, source and artifact trace custody.
2. Only then consume the Slice 07 consistency result alongside independently
   authenticated evidence. Do not treat the Python CI as host-qualification.

## Reproduction (pure CI)

python -m unittest tests.test_uhp_capture_intake -v
python -m unittest discover -s tests -v

No live host evidence or effects were collected in this release. All UHP
01–06 candidates are preserved; Ω 09M STABLE_WAIT, release eligibility
and canonical authority remain unchanged.
