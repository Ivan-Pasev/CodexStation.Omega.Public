# Omega UHP Slice 05 — Detached Observer Attestation Preflight

Date: 2026-11-05
State: draft candidate; offline tests; no dispatch; no release.
Predecessor: Slice 04 PR #32 head 7e365b11bc11d3d7503e9f79fe7a0a938505b65c.
Upstream reference: HarnessRouter v0.38.2; UHP 2026-10-19.
Provenance: original integration code; no imported upstream implementation.

## Scope

New runtime08c/uhp_observer_attestation.py provides
verify_detached_observer(review, envelope, trust, verification_key,
seen_nonces, evaluation_epoch). There is no production signing function.

It checks a detached HMAC-SHA256 envelope against a separately supplied
verification key, binds that envelope to the preceding Slice 04 receipt
digest, before/after snapshot digests, artifact digest, project, work order,
purpose, observer/key identifiers, short validity period and nonce set.
The result may be MAC_MATCH_CUSTODY_UNVERIFIED or HOLD.

## Crucial trust boundary

Symmetric HMAC is not proof of who signed. Anyone with the key could
forge a valid MAC. A caller-supplied trust record, evaluation timestamp,
or replay set does not constitute actual custody, independent observation,
trusted time, or a durable anti-replay journal. Even a syntactically
correct valid-MAC receipt reports:
- independent_observer_attested=false
- observer_key_custody_attested=false
- trusted_clock_attested=false
- durable_replay_attested=false
- source_capture_independence_attested=false
- external_effects_verified=false
- dispatch_authorized=false
- retry_authorized=false
- promotion_authorized=false
- canonical_authority_delta=NONE

The code does not collect files, manage a key, access network resources,
launch agents, verify a physical execution or transmit credentials.
Test-only fixtures generate a synthetic HMAC to exercise verification;
they are not test vectors for a deployed trusted signer.

## Threats / tests

Reject altered review receipts; wrong work order, project, observer or
key ID; changed artifact/source digests; malformed envelopes; unqualified
proof algorithms; bogus canonical authority; short keys and malformed
nonces. HOLD inactive/revoked trust record, stale or future envelope,
duplicate nonce in the supplied set, or wrong MAC.

The replay set has no persistent storage. No claim of actual anti-replay
protection is made.

## Required independent operational qualifications

1. Principal-separated observer running outside the executor sandbox.
2. Independently managed key custody and owner-approved scoped grants.
3. Independent file and process capture with bounded artifacts.
4. Verified TLS endpoint / exact host and environment version.
5. Atomic durable replay and trusted clock.
6. Credential isolation; actual network/file/tool limitations.
7. Independent effect observation and cost/privacy evidence.
8. Governance approval through existing Omega authority mechanisms.

For production multi-party verification, assess audited Ed25519 or
equivalent asymmetric attestation through protected signing facilities;
the HMAC example is a limited protocol preflight, not nonrepudiation.

## Verification

python -m unittest discover -s tests -v
python -m unittest -v tests.test_uhp_observer_attestation

No main merge, 09M reopening, installed release, live runtime qualification,
scientific admission or canonical authority promotion by this slice.
