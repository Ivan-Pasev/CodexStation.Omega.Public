# Omega UHP Slice 05 — External Observer Trust Boundary

Date: 2026-11-05
Status: OFFLINE SYNTHETIC / DRAFT PR / NO HOST OR CANON AUTHORITY
Parent: Slice 04 PR #32, head 7e365b11bc11d3d7503e9f79fe7a0a938505b65c
Upstream reference: HarnessRouter v0.38.2 and UHP 2026-10-19
Code provenance: original CodexStation implementation, no third-party source import.

## Interface

runtime08c/uhp_observer.py:
verify_observer_envelope(offline_review, envelope, anchor, replay_state)

A domain-separated canonical JSON HMAC-SHA256 is checked against a caller
supplied byte key. The claim binds exact project, work order, original source,
request/response digests, offline receipt and before/after/artifact manifests.
A claimed observer principal and host must differ from the agent principal
and host, and must match the supplied anchor. Replay state checks monotonic
sequence, nonce and predecessor-attestation digest. No state is persisted.

## Fundamental claim boundary

The key AND anchor are caller supplied. Matching a test HMAC is not proof
that a witness is independent, that keys are held separately, that the
claimed hosts exist, that a clock is trustworthy or that any physical
effects were observed. A forged anchor plus forged envelope can produce
the same cryptographic match. The result deliberately uses
OFFLINE_MAC_CONSISTENT_UNATTESTED, never AUTHENTICATED.

DISPATCH_AUTHORIZED=false
PROMOTION_AUTHORIZED=false
CANONICAL_AUTHORITY_DELTA=NONE
EXTERNAL_EFFECTS_VERIFIED=false
KEY_CUSTODY_VERIFIED=false
OBSERVER_INDEPENDENCE_VERIFIED=false
DURABLE_REPLAY_COMMITTED=false

This prototype has no HTTP client, agent/tool launcher, credential
storage, filesystem reader, model API or real execution behavior.
The key is not serialized in a receipt.

## Next operational gates

1. Replace test HMAC with an externally provisioned asymmetric Ed25519
   or hardware-backed attestation identity; pin verifier keys separately.
2. Run the collector under a distinct principal AND actually separate
   process/host trust boundary; prove capability denial.
3. Record genuine pre/post source bytes with verified provenance and
   immutable digest binding. Supply offline review only through this
   controlled capture channel.
4. Persist nonce/replay state durably and transactionally, enforce
   idempotency across restarts and network loss.
5. Qualify sandbox mounts, network egress, tool restrictions and secret
   isolation on disposable infrastructure, with negative tests.
6. Verify actual external effects, trace origin, metered costs and
   privacy impact independently from agent self-report.
7. Require independent governance authority and release approval.
   No observer may self-promote knowledge or releases.

## Reproduce

python -m unittest -v tests.test_uhp_observer
python -m unittest discover -s tests -v

All 09M stable-wait and inherited governance/release gates remain.
