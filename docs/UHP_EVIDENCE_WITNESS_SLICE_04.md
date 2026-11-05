# Omega UHP Slice 04 — Hermetic Evidence Review and Observer Boundary

Date: 2026-11-05
Status: STACKED DRAFT / SYNTHETIC / NON-DISPATCHING / NON-PROMOTING
Parent: UHP Slice 03 PR #31 head 7c7de793ed32d5905d7e802bdedc1b3e1b7d6558
Upstream reference: UHP 2026-10-19 / HarnessRouter v0.38.2
Licensing: original CodexStation integration code; no upstream source transplanted.

## Architectural objective

Introduce a bounded, deterministic, auditable *offline consistency checker*
for source snapshots and artifacts. It must not claim to be an independent
operational observer merely because its function name contains "witness".

Exports in runtime08c/uhp_witness.py:

- snapshot_manifest(files): SHA-256 of exact supplied bytes per path,
  followed by a domain-separated canonical manifest digest.
- review_offline_evidence(contract, transport, observation, before, after,
  artifact_claims, artifact_bytes): binds the previous 01-03 contracts,
  compares byte-backed before/after snapshots, and checks each claimed
  artifact against supplied bytes. It outputs only digests, path names,
  bounded change listings, and a non-authorizing review receipt.

## Security boundaries and scientific claims

1. Agent-reported success is not independently observed execution.
2. READ_ONLY task intent is not a filesystem or network sandbox guarantee.
3. A manifest of bytes supplied by the caller does not attest origin,
   independence, hardware identity, file creation time or custody.
4. A model claim of an artifact is not proof of the artifact: bytes must
   be supplied separately and exactly match the declared content digest.
5. A byte match means consistency of supplied evidence, never proof that
   physical files came from a specific machine or untouched source.
6. A changed source snapshot during a purported READ_ONLY task is HOLD.
7. A mismatched work order, request, transport or response hash is HOLD
   or fail-closed as appropriate.
8. A forged authorized dispatch, release, capability attestation or
   closed external gate is rejected, not accepted as new permission.
9. All verdicts preserve PROMOTION_AUTHORIZED=false,
   CANONICAL_AUTHORITY_DELTA=NONE, EXTERNAL_EFFECTS_VERIFIED=false.
10. No network, host-file reads, external credentials, plugin calls,
    local agents, live-model execution or canonical-state writes occur.

## Bounded evidence API

Each logical path is simple ASCII POSIX relative syntax, without traversal,
drive-letter paths, encoded separators or control characters. Values are
exact bytes, not text statements. At most 32 files and 128 KiB per file;
each supplied snapshot is bounded to 512 KiB. A receipt never includes raw
file bodies. SHA-256-shaped digests require correct contents to match but
do not replace external provenance.

Verdict states:
- OFFLINE_CONSISTENT_UNATTESTED: supplied bytes, declared artifacts and
  bound proposal observations are internally consistent; NOT independent
  proof and NOT permission.
- HOLD: source mutation, missing/unclaimed/tampered artifact bytes, or
  invalid/noncompleted task status.
- UHPContractError: structurally invalid, unbound or authority-smuggling
  inputs. A caller must translate this into HOLD rather than retry.

## Future independent witness gate

Implement a separately scoped observer outside the agent's sandbox that
captures exact before/after bytes in a disposable environment, signs or
otherwise authenticates its own provenance, verifies process/container
identity, network and tool restrictions, observes cost and effects, and
supplies evidence through a trusted ingestion pathway. Its attestations
must be independently checked, not inferred from an agent JSON field.
No external authority gate is closed by this offline candidate.

## Reproduce

python -m unittest -v tests.test_uhp_witness
python -m unittest discover -s tests -v

Do not merge this draft as 09M release certification. Source verification,
independent host/identity, real sandbox, idempotent transport, effects
observation, licensing and external evidence remain separately gated.
