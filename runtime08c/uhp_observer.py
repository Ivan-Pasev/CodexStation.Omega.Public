"""UHP observer envelope: offline HMAC consistency, NOT independent attestation.

All inputs including key and alleged trust anchor are caller-supplied.
Never performs I/O, host observation, execution, promotion, or key storage.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import re
from collections.abc import Mapping
from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_witness import REVIEW_SCHEMA

ENVELOPE_SCHEMA = "codexstation.omega.uhp.observer-envelope.v0.1"
CLAIM_SCHEMA = "codexstation.omega.uhp.observer-claim.v0.1"
RESULT_SCHEMA = "codexstation.omega.uhp.observer-review.v0.1"
DOMAIN = b"CODEXSTATION_OMEGA_UHP_OBSERVER_V01\x00"
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
IDENTITIES = ("observer_id", "observer_principal_id", "observer_host_id",
              "agent_principal_id", "agent_host_id", "scope")
BINDINGS = ("project_id", "work_order_id", "source_digest", "request_sha256",
            "response_sha256", "offline_receipt_digest", "before_digest",
            "after_digest", "artifact_digest")
PAYLOAD_FIELDS = set(IDENTITIES + BINDINGS) | {
    "schema", "sequence", "nonce", "previous_attestation_digest",
    "capture_start_unix", "capture_end_unix", "effects_claim",
}
ANCHOR_FIELDS = set(IDENTITIES) | {"mac_key"}
REPLAY_FIELDS = {"last_sequence", "last_digest", "seen_nonces"}


def _wire(value):
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise UHPContractError("observer_invalid_json") from exc
    if len(raw) > 32768:
        raise UHPContractError("observer_oversize")
    return raw


def _digest(value):
    return "sha256:" + hashlib.sha256(_wire(value)).hexdigest()


def _name(value, label):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise UHPContractError("invalid_" + label)


def _hash(value, label, expression=SHA):
    if not isinstance(value, str) or not expression.fullmatch(value):
        raise UHPContractError("invalid_" + label)


def _count(value, label):
    if type(value) is not int or value < 0:
        raise UHPContractError("invalid_" + label)


def _preflight(review, anchor, replay):
    if not isinstance(review, Mapping) or review.get("schema") != REVIEW_SCHEMA:
        raise UHPContractError("review_schema_invalid")
    recorded = review.get("receipt_digest")
    _hash(recorded, "receipt_digest")
    unsigned = dict(review)
    del unsigned["receipt_digest"]
    if not hmac.compare_digest(recorded, _digest(unsigned)):
        raise UHPContractError("review_digest_inconsistent")
    for field in ("project_id", "work_order_id"):
        _name(review.get(field), field)
    for field in ("bound_source_digest", "baseline_manifest_digest",
                  "observed_manifest_digest", "artifact_manifest_digest"):
        _hash(review.get(field), field)
    for field in ("bound_request_sha256", "bound_response_sha256"):
        _hash(review.get(field), field, HEX)
    for field in ("dispatch_authorized", "promotion_authorized",
                  "observer_identity_attested", "source_capture_independence_attested",
                  "external_effects_verified", "sandbox_enforcement_verified"):
        if review.get(field) is not False:
            raise UHPContractError("review_authority_smuggling")
    if review.get("canonical_authority_delta") != "NONE":
        raise UHPContractError("review_authority_delta")
    if review.get("effect_confirmation") != "UNKNOWN_OUTCOME":
        raise UHPContractError("review_effect_claim_smuggling")
    if review.get("verdict") not in ("HOLD", "OFFLINE_CONSISTENT_UNATTESTED"):
        raise UHPContractError("review_verdict_invalid")
    if not isinstance(anchor, Mapping) or set(anchor) != ANCHOR_FIELDS:
        raise UHPContractError("anchor_shape_invalid")
    for field in IDENTITIES:
        _name(anchor[field], field)
    key = anchor["mac_key"]
    if type(key) is not bytes or not 32 <= len(key) <= 128:
        raise UHPContractError("anchor_key_invalid")
    if anchor["observer_principal_id"] == anchor["agent_principal_id"]:
        raise UHPContractError("observer_not_separate_principal")
    if anchor["observer_host_id"] == anchor["agent_host_id"]:
        raise UHPContractError("observer_not_separate_host")
    if anchor["scope"] != "DISPOSABLE_READ_ONLY":
        raise UHPContractError("observer_scope_unqualified")
    if not isinstance(replay, Mapping) or set(replay) != REPLAY_FIELDS:
        raise UHPContractError("replay_shape_invalid")
    _count(replay["last_sequence"], "last_sequence")
    _hash(replay["last_digest"], "last_digest")
    nonces = replay["seen_nonces"]
    if (not isinstance(nonces, list) or len(nonces) > 64
            or any(not isinstance(x, str) or not TOKEN.fullmatch(x) for x in nonces)
            or len(set(nonces)) != len(nonces)):
        raise UHPContractError("replay_history_invalid")


def verify_observer_envelope(review: Mapping, envelope: Mapping,
                             anchor: Mapping, replay_state: Mapping):
    """Only report consistency with a SUPPLIED key, never trusted witness identity."""
    _preflight(review, anchor, replay_state)
    if not isinstance(envelope, Mapping) or set(envelope) != {
        "schema", "alg", "payload", "mac",
    }:
        raise UHPContractError("envelope_shape_invalid")
    if envelope["schema"] != ENVELOPE_SCHEMA or envelope["alg"] != "HMAC-SHA256":
        raise UHPContractError("algorithm_or_schema_invalid")
    _hash(envelope["mac"], "mac", HEX)
    p = envelope["payload"]
    if not isinstance(p, Mapping) or set(p) != PAYLOAD_FIELDS:
        raise UHPContractError("claim_shape_invalid")
    if p.get("schema") != CLAIM_SCHEMA:
        raise UHPContractError("claim_schema_invalid")
    for field in IDENTITIES + ("project_id", "work_order_id", "nonce"):
        _name(p[field], field)
    for field in ("source_digest", "offline_receipt_digest",
                  "before_digest", "after_digest", "artifact_digest",
                  "previous_attestation_digest"):
        _hash(p[field], field)
    for field in ("request_sha256", "response_sha256"):
        _hash(p[field], field, HEX)
    for field in ("sequence", "capture_start_unix", "capture_end_unix"):
        _count(p[field], field)
    if (p["capture_end_unix"] < p["capture_start_unix"]
            or p["capture_end_unix"] - p["capture_start_unix"] > 3600):
        raise UHPContractError("capture_window_invalid")
    if p["effects_claim"] != "NO_EXTERNAL_EFFECTS_CLAIMED":
        raise UHPContractError("effects_claim_unqualified")

    reasons = []
    if any(p[field] != anchor[field] for field in IDENTITIES):
        reasons.append("ANCHOR_BINDING_MISMATCH")
    expected = {
        "project_id": review["project_id"],
        "work_order_id": review["work_order_id"],
        "source_digest": review["bound_source_digest"],
        "request_sha256": review["bound_request_sha256"],
        "response_sha256": review["bound_response_sha256"],
        "offline_receipt_digest": review["receipt_digest"],
        "before_digest": review["baseline_manifest_digest"],
        "after_digest": review["observed_manifest_digest"],
        "artifact_digest": review["artifact_manifest_digest"],
    }
    if any(p[k] != v for k, v in expected.items()):
        reasons.append("EVIDENCE_BINDING_MISMATCH")
    if review["verdict"] != "OFFLINE_CONSISTENT_UNATTESTED":
        reasons.append("OFFLINE_REVIEW_NOT_CONSISTENT")
    if review["baseline_manifest_digest"] != review["observed_manifest_digest"]:
        reasons.append("SOURCE_CHANGED")
    if p["sequence"] != replay_state["last_sequence"] + 1:
        reasons.append("SEQUENCE_GAP_OR_REPLAY")
    if p["previous_attestation_digest"] != replay_state["last_digest"]:
        reasons.append("PREVIOUS_ATTESTATION_MISMATCH")
    if p["nonce"] in replay_state["seen_nonces"]:
        reasons.append("NONCE_REPLAY")
    computed = hmac.new(anchor["mac_key"], DOMAIN + _wire(dict(p)),
                        hashlib.sha256).hexdigest()
    match = hmac.compare_digest(computed, envelope["mac"])
    if not match:
        reasons.append("SUPPLIED_KEY_MAC_MISMATCH")

    eid = _digest({"schema": envelope["schema"], "alg": envelope["alg"],
                   "payload": dict(p), "mac": envelope["mac"]})
    return {
        "schema": RESULT_SCHEMA,
        "verdict": "HOLD" if reasons else "OFFLINE_MAC_CONSISTENT_UNATTESTED",
        "reasons": sorted(set(reasons)),
        "attestation_digest": eid,
        "bound_offline_receipt_digest": review["receipt_digest"],
        "mac_matches_supplied_key": match,
        "claimed_separate_host_and_principal": (
            p["observer_host_id"] != p["agent_host_id"]
            and p["observer_principal_id"] != p["agent_principal_id"]
        ),
        "observer_identity_independently_attested": False,
        "observer_host_independently_attested": False,
        "key_custody_verified": False,
        "clock_trusted": False,
        "durable_replay_committed": False,
        "sandbox_enforcement_verified": False,
        "external_effects_verified": False,
        "dispatch_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
        "candidate_replay_state": (
            {"last_sequence": p["sequence"], "last_digest": eid,
             "seen_nonces": (replay_state["seen_nonces"] + [p["nonce"]])[-64:]}
            if not reasons else None
        ),
    }
