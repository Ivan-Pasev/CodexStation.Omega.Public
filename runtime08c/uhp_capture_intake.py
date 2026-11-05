"""Slice 07: evaluate *supplied* probe-event bytes, without live host access.

This is a bounded, zero-I/O intake validator. It DOES NOT capture events,
authenticate an observer, attest a host, sign receipts, write replay state,
start a sandbox, dispatch a model, or authorize promotion. Honest input can
be internally consistent, but a forged input can also be self-consistent.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping

from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_host_qualification import assess_report
from runtime08c.uhp_witness import snapshot_manifest

CAPTURE_SCHEMA = "codexstation.omega.uhp.capture-claim.v0.1"
EVENT_SCHEMA = "codexstation.omega.uhp.probe-event.v0.1"
REVIEW_SCHEMA = "codexstation.omega.uhp.capture-intake-review.v0.1"
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.json\Z")
FIELDS = frozenset({
    "schema", "plan_digest", "observer_host_id", "observer_principal_id",
    "executor_host_id", "executor_principal_id", "collector_session",
    "event_refs", "source_before_digest", "source_after_digest",
})
EVENT_FIELDS = frozenset({
    "schema", "plan_digest", "probe_id", "observed",
    "observer_host_id", "observer_principal_id", "executor_host_id",
    "executor_principal_id", "collector_session", "sequence",
    "capture_epoch", "nonce",
})
LINK_FIELDS = (
    "observer_host_id", "observer_principal_id",
    "executor_host_id", "executor_principal_id",
)


def _text(value, label):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise UHPContractError("invalid_" + label)
    return value


def _digest(value):
    try:
        b = json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":"), allow_nan=False).encode("ascii")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise UHPContractError("intake_not_json") from exc
    if len(b) > 32768:
        raise UHPContractError("intake_json_unbounded")
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _no_duplicate_keys(pairs):
    value = {}
    for k, v in pairs:
        if k in value:
            raise UHPContractError("duplicate_event_key")
        value[k] = v
    return value


def _parse_event(raw):
    if type(raw) is not bytes or len(raw) > 4096:
        raise UHPContractError("invalid_event_bytes")
    try:
        event = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")),
        )
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError) as exc:
        raise UHPContractError("event_not_strict_json") from exc
    if not isinstance(event, dict) or set(event) != EVENT_FIELDS:
        raise UHPContractError("event_shape_invalid")
    if event.get("schema") != EVENT_SCHEMA:
        raise UHPContractError("event_schema_invalid")
    for field in ("plan_digest", "probe_id", "observer_host_id",
                  "observer_principal_id", "executor_host_id",
                  "executor_principal_id", "collector_session", "nonce"):
        _text(event[field], field)
    if type(event["sequence"]) is not int or not 1 <= event["sequence"] <= 32:
        raise UHPContractError("event_sequence_invalid")
    if type(event["capture_epoch"]) is not int or event["capture_epoch"] < 0:
        raise UHPContractError("event_timestamp_invalid")
    if event["observed"] not in (
        "DENIED", "REJECTED", "NO_AUTO_RETRY", "MATCH", "ALLOWED", "UNKNOWN",
    ):
        raise UHPContractError("event_outcome_invalid")
    return event


def evaluate_capture_intake(plan: Mapping, matrix: Mapping, report: Mapping,
                            capture: Mapping, evidence_bytes: Mapping,
                            before_bytes: Mapping, after_bytes: Mapping):
    """Only accept internally complete input and return NEVER-AUTHORIZING review.

    Evidence bytes and snapshots originate from the caller. The intake
    deliberately never promotes to VERIFIED or PASS; a real observer trust
    registry, protected capture and durable replay are external gates.
    """
    prior = assess_report(plan, matrix, report)
    if not isinstance(capture, Mapping) or set(capture) != FIELDS:
        raise UHPContractError("capture_contract_invalid")
    if capture["schema"] != CAPTURE_SCHEMA:
        raise UHPContractError("capture_schema_invalid")
    if capture["plan_digest"] != plan["plan_digest"]:
        raise UHPContractError("capture_plan_digest_mismatch")
    config = plan["config"]
    for field in LINK_FIELDS:
        _text(capture.get(field), field)
        if capture[field] != config[field]:
            raise UHPContractError("capture_identity_binding_mismatch")
    _text(capture["collector_session"], "collector_session")
    refs = capture["event_refs"]
    if (not isinstance(refs, list) or len(refs) != len(plan["negative_probes"])
            or not all(isinstance(ref, str) and REF.fullmatch(ref) for ref in refs)
            or len(refs) != len(set(refs))):
        raise UHPContractError("invalid_capture_event_inventory")
    if not isinstance(evidence_bytes, Mapping) or set(refs) != set(evidence_bytes):
        raise UHPContractError("capture_bytes_missing_or_orphaned")
    for raw in evidence_bytes.values():
        if type(raw) is not bytes or len(raw) > 4096:
            raise UHPContractError("capture_event_size_or_type_invalid")
    event_manifest = snapshot_manifest(evidence_bytes)
    before = snapshot_manifest(before_bytes)
    after = snapshot_manifest(after_bytes)
    for field, digest in (("source_before_digest", before["digest"]),
                          ("source_after_digest", after["digest"])):
        if capture[field] != digest:
            raise UHPContractError("capture_source_digest_claim_mismatch")

    reasons = list(prior["reasons"])
    if before["digest"] != config["source_digest"]:
        reasons.append("SOURCE_PRE_CAPTURE_DIFFERS_FROM_PIN")
    if before["digest"] != after["digest"]:
        reasons.append("SOURCE_MUTATED_IN_SUPPLIED_SNAPSHOTS")
    expected = {p["id"]: p["expected"] for p in plan["negative_probes"]}
    claims = {p["id"]: p for p in report["probes"]}
    visited = set()
    nonces = set()
    last_time = None
    for i, ref in enumerate(refs, 1):
        evt = _parse_event(evidence_bytes[ref])
        probe = evt["probe_id"]
        if probe not in expected or probe in visited:
            raise UHPContractError("capture_unknown_or_repeated_probe")
        visited.add(probe)
        if evt["plan_digest"] != plan["plan_digest"]:
            reasons.append("EVENT_PLAN_BINDING_MISMATCH")
        for field in LINK_FIELDS:
            if evt[field] != capture[field]:
                reasons.append("EVENT_OBSERVER_EXECUTOR_BINDING_MISMATCH")
                break
        if evt["collector_session"] != capture["collector_session"]:
            reasons.append("EVENT_COLLECTOR_SESSION_MISMATCH")
        if evt["sequence"] != i:
            reasons.append("EVENT_SEQUENCE_GAP")
        if evt["nonce"] in nonces:
            reasons.append("EVENT_NONCE_DUPLICATE_IN_CAPTURE")
        nonces.add(evt["nonce"])
        if last_time is not None and evt["capture_epoch"] < last_time:
            reasons.append("EVENT_TIMESTAMP_OUT_OF_ORDER")
        last_time = evt["capture_epoch"]
        if evt["observed"] != expected[probe]:
            reasons.append("NEGATIVE_PROBE_FAILED_IN_CAPTURE")
        claim = claims.get(probe)
        if not isinstance(claim, Mapping) or claim.get("evidence_ref") != ref:
            reasons.append("REPORT_EVIDENCE_REFERENCE_MISMATCH")
        if not isinstance(claim, Mapping) or claim.get("observed") != evt["observed"]:
            reasons.append("REPORT_EVENT_OUTCOME_MISMATCH")
    if visited != set(expected):
        reasons.append("CAPTURE_PROBES_INCOMPLETE")
    if prior["verdict"] != "CLAIMS_COMPLETE_INDEPENDENT_PROOF_REQUIRED":
        reasons.append("PRIOR_QUALIFICATION_REPORT_NOT_COMPLETE")
    result = {
        "schema": REVIEW_SCHEMA,
        "plan_digest": plan["plan_digest"],
        "work_order_id": config["work_order_id"],
        "project_id": config["project_id"],
        "probe_event_count": len(visited),
        "evidence_manifest_digest": event_manifest["digest"],
        "source_before_digest": before["digest"],
        "source_after_digest": after["digest"],
        "verdict": ("HOLD" if reasons
                    else "CAPTURE_BYTES_CONSISTENT_INDEPENDENCE_HOLD"),
        "reasons": sorted(set(reasons)),
        "supplied_bytes_hashed": True,
        "capture_provenance_independently_verified": False,
        "observer_host_independently_verified": False,
        "observer_key_custody_verified": False,
        "technical_sandbox_enforcement_verified": False,
        "trusted_timestamp_verified": False,
        "durable_replay_committed": False,
        "independent_effects_verified": False,
        "actual_host_run_performed_by_this_api": False,
        "dispatch_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
    }
    result["review_digest"] = _digest(result)
    return result
