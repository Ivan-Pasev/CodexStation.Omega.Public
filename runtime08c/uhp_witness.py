"""Hermetic CodexStation Omega UHP evidence cross-checking; NO live witness.

Data are supplied as bytes by the caller. Hashing them verifies consistency,
NOT collection independence, machine identity, sandbox isolation, or an effect.
Never does network, filesystem, process, token, approval, or canon operations.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping

from runtime08c.uhp_adapter import UHPContractError

SNAPSHOT_SCHEMA = "codexstation.omega.uhp.byte-snapshot.v0.1"
REVIEW_SCHEMA = "codexstation.omega.uhp.offline-evidence-review.v0.1"
_PATH = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*\Z")
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")


def _hash_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_hash(value):
    try:
        wire = json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise UHPContractError("non_json_witness") from exc
    if len(wire) > 32768:
        raise UHPContractError("unbounded_witness")
    return _hash_bytes(wire)


def _path(name):
    if not isinstance(name, str) or len(name) > 255 or not _PATH.fullmatch(name):
        raise UHPContractError("unsafe_witness_path")
    if any(segment in (".", "..") for segment in name.split("/")):
        raise UHPContractError("traversal_witness_path")
    return name


def snapshot_manifest(files: Mapping):
    """Digest a caller-supplied finite map of logical path -> exact bytes.

    Explicit size limits prevent unbounded data from reaching this verifier.
    There is no host filesystem inspection and no independent provenance.
    """
    if not isinstance(files, Mapping):
        raise UHPContractError("invalid_witness_snapshot")
    if len(files) > 32:
        raise UHPContractError("too_many_witness_files")
    entries = []
    total = 0
    for name, content in files.items():
        name = _path(name)
        if not isinstance(content, bytes) or len(content) > 131072:
            raise UHPContractError("unbounded_or_nonbyte_witness_file")
        total += len(content)
        if total > 524288:
            raise UHPContractError("witness_snapshot_too_large")
        entries.append({"path": name, "bytes": len(content),
                        "sha256": _hash_bytes(content)})
    entries.sort(key=lambda e: e["path"])
    statement = {"schema": SNAPSHOT_SCHEMA, "entries": entries}
    return {
        "schema": SNAPSHOT_SCHEMA,
        "digest": _canonical_hash(statement),
        "files": len(entries), "bytes": total,
        "entries": entries,
        "source_bytes_independently_acquired": False,
    }


def _require_bound_contract(contract, transport, observation, baseline):
    """Reject authority smuggling, cross-order binding and forged gate closures."""
    if not all(isinstance(x, Mapping) for x in
               (contract, transport, observation)):
        raise UHPContractError("invalid_witness_contract_inputs")
    if contract.get("schema") != "codexstation.omega.uhp.proposal.v0.1":
        raise UHPContractError("witness_contract_schema_invalid")
    if transport.get("schema") != "codexstation.omega.uhp.transport-preview.v0.1":
        raise UHPContractError("witness_transport_schema_invalid")
    if observation.get("schema") != "codexstation.omega.uhp.execution-observation.v0.1":
        raise UHPContractError("witness_observation_schema_invalid")
    for obj in (contract, transport, observation):
        if obj.get("dispatch_authorized") is not False:
            raise UHPContractError("witness_dispatch_smuggling")
        if obj.get("canonical_authority_delta") != "NONE":
            raise UHPContractError("witness_authority_smuggling")
    if transport.get("retry_authorized") is not False:
        raise UHPContractError("witness_retry_smuggling")
    if observation.get("promotion_authorized") is not False:
        raise UHPContractError("witness_promotion_smuggling")
    if transport.get("static_verdict") != "SHAPE_PASS_EXTERNAL_GATES_HOLD":
        raise UHPContractError("witness_unqualified_transport")
    if contract.get("protocol_version") != "2026-10-19":
        raise UHPContractError("witness_protocol_mismatch")
    for name in ("project_id", "work_order_id", "request_sha256",
                 "work_order_sha256", "source_digest"):
        if contract.get(name) != transport.get(name):
            raise UHPContractError("witness_transport_binding_mismatch_" + name)
    if observation.get("work_order_id") != contract.get("work_order_id"):
        raise UHPContractError("witness_observation_work_order_mismatch")
    if contract.get("source_digest") != baseline["digest"]:
        raise UHPContractError("source_manifest_digest_mismatch")
    if not isinstance(contract.get("request_sha256"), str) or not _HEX.fullmatch(contract["request_sha256"]):
        raise UHPContractError("invalid_bound_request_hash")
    if not isinstance(observation.get("response_sha256"), str) or not _HEX.fullmatch(observation["response_sha256"]):
        raise UHPContractError("invalid_bound_response_hash")
    gates = transport.get("external_gates")
    if not isinstance(gates, Mapping) or not gates or any(v != "HOLD" for v in gates.values()):
        raise UHPContractError("forged_external_gate_closure")
    if (observation.get("evidence_status") != "UNVERIFIED"
            or observation.get("server_identity_attested") is not False
            or observation.get("source_content_verified") is not False
            or observation.get("read_only_enforcement") != "NOT_ATTESTED"):
        raise UHPContractError("forged_witness_attestation")


def review_offline_evidence(contract: Mapping, transport: Mapping,
                            observation: Mapping, before: Mapping,
                            after: Mapping, artifact_claims: list,
                            artifact_bytes: Mapping):
    """Compare exact supplied data. No caller is trusted as an actual witness.

    before/after are *claimed* source snapshots. Separate artifact_bytes
    supplies the bytes against which a claim can be checked; this separation
    does not prove they came from independent collection or hardware.
    """
    baseline = snapshot_manifest(before)
    result = snapshot_manifest(after)
    supplied = snapshot_manifest(artifact_bytes)
    _require_bound_contract(contract, transport, observation, baseline)
    if not baseline["entries"]:
        raise UHPContractError("empty_baseline_not_qualified")
    if not isinstance(artifact_claims, list) or len(artifact_claims) > 32:
        raise UHPContractError("invalid_artifact_claims")

    expected = {}
    for claim in artifact_claims:
        if not isinstance(claim, Mapping) or set(claim) != {"path", "sha256"}:
            raise UHPContractError("invalid_artifact_claim")
        path = _path(claim["path"])
        if path in expected:
            raise UHPContractError("duplicate_artifact_claim")
        claimed = claim["sha256"]
        if not isinstance(claimed, str) or not _SHA.fullmatch(claimed):
            raise UHPContractError("invalid_artifact_digest")
        expected[path] = claimed

    pre = {e["path"]: e["sha256"] for e in baseline["entries"]}
    post = {e["path"]: e["sha256"] for e in result["entries"]}
    supplied_artifacts = {e["path"]: e["sha256"] for e in supplied["entries"]}
    changed = sorted(p for p in set(pre) | set(post) if pre.get(p) != post.get(p))
    reasons = []
    if changed:
        reasons.append("READ_ONLY_SOURCE_MUTATION_IN_SUPPLIED_SNAPSHOTS")
    if observation.get("verdict") != "TASK_COMPLETED_EFFECT_UNVERIFIED":
        reasons.append("TASK_NOT_CLEANLY_COMPLETED")
    if observation.get("uhp_status") != "completed":
        reasons.append("TASK_LIFECYCLE_NOT_COMPLETE")
    if observation.get("effect_confirmation") != "UNKNOWN_OUTCOME":
        reasons.append("EFFECT_STATUS_CONTRACT_MISMATCH")
    missing = sorted(set(expected) - set(supplied_artifacts))
    unexpected = sorted(set(supplied_artifacts) - set(expected))
    different = sorted(p for p in set(expected) & set(supplied_artifacts)
                       if expected[p] != supplied_artifacts[p])
    if missing:
        reasons.append("ARTIFACT_BYTES_MISSING")
    if unexpected:
        reasons.append("UNDECLARED_ARTIFACT_BYTES")
    if different:
        reasons.append("ARTIFACT_CONTENT_DIGEST_MISMATCH")
    evidence = {
        "schema": REVIEW_SCHEMA,
        "work_order_id": contract["work_order_id"],
        "project_id": contract["project_id"],
        "bound_source_digest": baseline["digest"],
        "bound_request_sha256": contract["request_sha256"],
        "bound_response_sha256": observation["response_sha256"],
        "baseline_manifest_digest": baseline["digest"],
        "observed_manifest_digest": result["digest"],
        "artifact_manifest_digest": supplied["digest"],
        "source_changes": changed,
        "missing_artifacts": missing,
        "unexpected_artifacts": unexpected,
        "digest_mismatched_artifacts": different,
        "verdict": ("HOLD" if reasons else "OFFLINE_CONSISTENT_UNATTESTED"),
        "reasons": reasons,
        "bytes_hashed_from_supplied_data": True,
        "observer_identity_attested": False,
        "source_capture_independence_attested": False,
        "external_effects_verified": False,
        "sandbox_enforcement_verified": False,
        "artifact_claims_authoritative": False,
        "effect_confirmation": "UNKNOWN_OUTCOME",
        "dispatch_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
    }
    evidence["receipt_digest"] = _canonical_hash(evidence)
    return evidence
