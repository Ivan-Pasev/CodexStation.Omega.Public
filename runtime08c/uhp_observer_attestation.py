"""Offline detached observer MAC validation; no signing, runtime or permissions.

A valid symmetric MAC binds bytes to a supplied verification key, NOT to an
independent person or machine. Key custody, capture and replay remain unproved.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import re
from collections.abc import Mapping

from runtime08c.uhp_adapter import UHPContractError

ENVELOPE_SCHEMA = "codexstation.omega.uhp.detached-observer.v0.1"
REVIEW_SCHEMA = "codexstation.omega.uhp.offline-evidence-review.v0.1"
DOMAIN = b"CS-OMEGA-UHP-OBSERVER-05\x00"
FIELDS = frozenset({
    "schema", "observer_id", "key_id", "project_id", "work_order_id",
    "receipt_digest", "source_digest", "after_digest", "artifact_digest",
    "nonce", "issued_at", "expires_at", "purpose", "algorithm", "mac",
})
TRUST_FIELDS = frozenset({
    "observer_id", "key_id", "project_id", "purpose", "status",
    "valid_from", "valid_until",
})
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
ID = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z")
NONCE = re.compile(r"[A-Za-z0-9_-]{32,96}\Z")
PURPOSE = "OFFLINE_CONSISTENCY"


def _bytes(value):
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")
    except (TypeError, ValueError, OverflowError, RecursionError) as e:
        raise UHPContractError("unserializable_observer_record") from e
    if len(data) > 32768:
        raise UHPContractError("oversized_observer_record")
    return data


def _digest(value):
    return "sha256:" + hashlib.sha256(_bytes(value)).hexdigest()


def _id(value):
    if not isinstance(value, str) or ID.fullmatch(value) is None:
        raise UHPContractError("invalid_observer_identifier")


def _hash(value):
    if not isinstance(value, str) or DIGEST.fullmatch(value) is None:
        raise UHPContractError("invalid_observer_digest")


def _time(value):
    if type(value) is not int or value < 0:
        raise UHPContractError("invalid_observer_timestamp")
    return value


def verify_detached_observer(review: Mapping, envelope: Mapping,
                             trust: Mapping, verification_key: bytes,
                             seen_nonces: frozenset, evaluation_epoch: int):
    """Check a detached HMAC against a caller-supplied key and trust record.

    Production module never signs; independent custody is NOT established by
    passing a trust record, and this method never returns authority to act.
    """
    if not all(isinstance(x, Mapping) for x in (review, envelope, trust)):
        raise UHPContractError("invalid_observer_input")
    if set(envelope) != FIELDS or set(trust) != TRUST_FIELDS:
        raise UHPContractError("observer_schema_mismatch")
    if not isinstance(verification_key, bytes) or len(verification_key) < 32:
        raise UHPContractError("invalid_verification_key")
    if type(seen_nonces) is not frozenset or len(seen_nonces) > 4096:
        raise UHPContractError("invalid_replay_snapshot")
    if not all(isinstance(n, str) and NONCE.fullmatch(n) for n in seen_nonces):
        raise UHPContractError("malformed_replay_snapshot")
    now = _time(evaluation_epoch)
    if review.get("schema") != REVIEW_SCHEMA or (
        review.get("verdict") != "OFFLINE_CONSISTENT_UNATTESTED"
    ):
        raise UHPContractError("unqualified_evidence_review")
    for field in ("dispatch_authorized", "promotion_authorized",
                  "external_effects_verified", "observer_identity_attested",
                  "source_capture_independence_attested",
                  "sandbox_enforcement_verified", "artifact_claims_authoritative"):
        if review.get(field) is not False:
            raise UHPContractError("claimed_authority_" + field)
    if (review.get("bytes_hashed_from_supplied_data") is not True
            or review.get("effect_confirmation") != "UNKNOWN_OUTCOME"
            or review.get("canonical_authority_delta") != "NONE"):
        raise UHPContractError("forged_effect_or_source_status")
    _hash(review.get("receipt_digest"))
    raw_review = {k: v for k, v in review.items() if k != "receipt_digest"}
    if _digest(raw_review) != review["receipt_digest"]:
        raise UHPContractError("modified_review_record")
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        raise UHPContractError("unrecognized_envelope")
    for name in ("observer_id", "key_id", "project_id", "work_order_id"):
        _id(envelope.get(name))
    for name in ("observer_id", "key_id", "project_id"):
        _id(trust.get(name))
        if trust[name] != envelope[name]:
            raise UHPContractError("principal_scope_mismatch")
    if (envelope["project_id"] != review.get("project_id") or
            envelope["work_order_id"] != review.get("work_order_id")):
        raise UHPContractError("wrong_receipt_scope")
    for name, receipt_name in (
        ("receipt_digest", "receipt_digest"),
        ("source_digest", "baseline_manifest_digest"),
        ("after_digest", "observed_manifest_digest"),
        ("artifact_digest", "artifact_manifest_digest"),
    ):
        _hash(envelope.get(name))
        if envelope[name] != review.get(receipt_name):
            raise UHPContractError("receipt_binding_mismatch")
    nonce = envelope.get("nonce")
    if not isinstance(nonce, str) or NONCE.fullmatch(nonce) is None:
        raise UHPContractError("invalid_nonce")
    issued = _time(envelope.get("issued_at"))
    expires = _time(envelope.get("expires_at"))
    start = _time(trust.get("valid_from"))
    end = _time(trust.get("valid_until"))
    if not issued < expires <= issued + 300 or not start < end:
        raise UHPContractError("invalid_attestation_window")
    if (envelope.get("purpose") != PURPOSE or trust.get("purpose") != PURPOSE
            or envelope.get("algorithm") != "HMAC-SHA256"):
        raise UHPContractError("unsupported_purpose_or_mac_algorithm")
    mac = envelope.get("mac")
    if not isinstance(mac, str) or re.fullmatch(r"[0-9a-f]{64}", mac) is None:
        raise UHPContractError("malformed_mac")
    unsigned = {k: envelope[k] for k in FIELDS if k != "mac"}
    actual = hmac.new(verification_key, DOMAIN + _bytes(unsigned),
                      hashlib.sha256).hexdigest()
    matched = hmac.compare_digest(mac, actual)
    reasons = []
    if not matched:
        reasons.append("AUTHENTICATOR_MISMATCH")
    if trust["status"] != "ACTIVE":
        reasons.append("INACTIVE_TRUST_RECORD")
    if not start <= issued <= now <= end:
        reasons.append("TRUST_WINDOW_FAILURE")
    if not issued - 30 <= now <= expires:
        reasons.append("ENVELOPE_WINDOW_FAILURE")
    if nonce in seen_nonces:
        reasons.append("NONCE_PRESENT_IN_SUPPLIED_SNAPSHOT")
    return {
        "schema": "codexstation.omega.uhp.observer-review.v0.1",
        "verdict": "HOLD" if reasons else "MAC_MATCH_CUSTODY_UNVERIFIED",
        "reasons": reasons,
        "review_receipt_digest": review["receipt_digest"],
        "envelope_digest": _digest(dict(envelope)),
        "mac_matched_supplied_key": matched,
        "independent_observer_attested": False,
        "observer_key_custody_attested": False,
        "trusted_clock_attested": False,
        "durable_replay_attested": False,
        "source_capture_independence_attested": False,
        "external_effects_verified": False,
        "dispatch_authorized": False,
        "retry_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
    }
