"""Offline UHP transport *preview*, never an HTTP client or authority grant.

All inputs may be attacker-supplied. This module has no network, filesystem,
credential, timing, process, or approval operations. A passing static shape
check is not a runtime, identity, privilege, source, or effects attestation.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping

from runtime08c.uhp_adapter import (
    UHPContractError,
    UHP_VERSION,
    analyze_discovery,
)

_REQUEST_KEYS = {
    "input", "model", "metadata", "stream", "store",
    "max_step", "timeout_seconds",
}
_CONTRACT_SCHEMA = "codexstation.omega.uhp.proposal.v0.1"
_TRANSPORT_SCHEMA = "codexstation.omega.uhp.transport-preview.v0.1"
_RETRY_STATES = {
    "NOT_SENT", "UNKNOWN_OUTCOME", "IN_PROGRESS", "COMPLETED",
    "FAILED", "INCOMPLETE", "CANCELLED",
}


def _sha(obj):
    try:
        value = json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise UHPContractError("not_canonical_json") from exc
    if len(value) > 32_768:
        raise UHPContractError("transport_body_unbounded")
    return hashlib.sha256(value).hexdigest()


def _text(value, name, maximum=128):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise UHPContractError("invalid_" + name)
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise UHPContractError("control_character_" + name)
    return value


def compile_transport_preview(request: Mapping, contract: Mapping,
                              discovery: Mapping):
    """Describe a pinned UHP HTTP request without dispatching it.

    The discovery document MUST be treated as untrusted and unauthenticated:
    even static PASS produces a permanent HOLD pending independent controls.
    """
    if not all(isinstance(x, Mapping) for x in (request, contract, discovery)):
        raise UHPContractError("invalid_transport_inputs")
    if set(request) != _REQUEST_KEYS:
        raise UHPContractError("request_shape_mismatch")
    if contract.get("schema") != _CONTRACT_SCHEMA:
        raise UHPContractError("contract_schema_mismatch")
    if contract.get("protocol_version") != UHP_VERSION:
        raise UHPContractError("protocol_version_mismatch")
    if contract.get("dispatch_authorized") is not False:
        raise UHPContractError("dispatch_authorization_smuggling")
    if contract.get("canonical_authority_delta") != "NONE":
        raise UHPContractError("authority_mutation_smuggling")
    if contract.get("effect_confirmation") != "NOT_OBSERVED":
        raise UHPContractError("effect_confirmation_smuggling")
    if contract.get("capability_claim") != "UNATTESTED":
        raise UHPContractError("forged_capability_attestation")

    project_id = _text(contract.get("project_id"), "project_id")
    work_order_id = _text(contract.get("work_order_id"), "work_order_id")
    for label in ("source_digest", "request_sha256", "work_order_sha256"):
        value = contract.get(label)
        pattern = r"sha256:[0-9a-f]{64}" if label == "source_digest" else r"[0-9a-f]{64}"
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            raise UHPContractError("invalid_" + label)

    actual_request_digest = _sha(dict(request))
    if actual_request_digest != contract.get("request_sha256"):
        raise UHPContractError("request_digest_mismatch")

    metadata = request.get("metadata")
    if not isinstance(metadata, Mapping):
        raise UHPContractError("invalid_metadata")
    if set(metadata) not in ({"harness_id"}, {"harness_id", "environment"}):
        raise UHPContractError("metadata_fields_not_qualified")
    if metadata.get("harness_id") != contract.get("expected_harness_id"):
        raise UHPContractError("harness_binding_mismatch")
    _text(metadata.get("harness_id"), "harness_id")
    expected_environment = contract.get("expected_environment")
    if metadata.get("environment") != expected_environment:
        raise UHPContractError("environment_binding_mismatch")
    if expected_environment is not None:
        _text(expected_environment, "environment")

    if request.get("model") != contract.get("expected_model"):
        raise UHPContractError("model_binding_mismatch")
    _text(request.get("model"), "model")
    if request.get("stream") is not False or request.get("store") is not False:
        raise UHPContractError("unsupported_stream_or_store")
    if not isinstance(request.get("input"), str) or not request["input"].strip():
        raise UHPContractError("invalid_task_input")
    if len(request["input"]) > 8192:
        raise UHPContractError("task_input_unbounded")
    for field, low, high in (
        ("max_step", 1, 8), ("timeout_seconds", 1, 300),
    ):
        value = request.get(field)
        if type(value) is not int or not low <= value <= high:
            raise UHPContractError("budget_out_of_bounds")

    shape = analyze_discovery(discovery)
    if shape["syntactic_compatibility"] != "PASS":
        raise UHPContractError("discovery_shape_unqualified")
    if discovery.get("capabilities", {}).get("idempotency") is not True:
        raise UHPContractError("idempotency_unadvertised")

    # Stable across the same proposal and scoped to its project/order/contents.
    # This is a correlation key, not cryptographic authorization or uniqueness
    # across services/principals. A future durable journal is mandatory.
    key_digest = _sha({
        "schema": _TRANSPORT_SCHEMA, "project_id": project_id,
        "work_order_id": work_order_id,
        "source_digest": contract["source_digest"],
        "request_sha256": actual_request_digest,
    })
    key = "csuhp03-" + key_digest[:48]
    return {
        "schema": _TRANSPORT_SCHEMA,
        "static_verdict": "SHAPE_PASS_EXTERNAL_GATES_HOLD",
        "dispatch_authorized": False,
        "retry_authorized": False,
        "canonical_authority_delta": "NONE",
        "work_order_id": work_order_id,
        "project_id": project_id,
        "request_sha256": actual_request_digest,
        "work_order_sha256": contract["work_order_sha256"],
        "source_digest": contract["source_digest"],
        "idempotency_key": key,
        "method": "POST",
        "relative_path": "/v1/responses",
        "headers": {
            "UHP-Version": UHP_VERSION,
            "Content-Type": "application/json",
            "Idempotency-Key": key,
        },
        # Does not serialize the user payload or any bearer token.
        "body_included": False,
        "target_host_included": False,
        "authorization_header_included": False,
        "external_gates": {
            "server_identity": "HOLD",
            "principal_scope": "HOLD",
            "harness_permissions": "HOLD",
            "source_content": "HOLD",
            "hard_tool_enforcement": "HOLD",
            "sandbox_isolation": "HOLD",
            "secret_custody": "HOLD",
            "durable_idempotency": "HOLD",
            "effects_witness": "HOLD",
        },
    }


def assess_retry(previous: Mapping, current: Mapping, last_state: str):
    """No retry is ever authorized; flag same-order/different-body collisions."""
    if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
        raise UHPContractError("invalid_retry_inputs")
    if last_state not in _RETRY_STATES:
        raise UHPContractError("invalid_retry_state")
    fields = (
        "schema", "project_id", "work_order_id",
        "request_sha256", "source_digest", "idempotency_key",
    )
    if any(field not in previous or field not in current for field in fields):
        raise UHPContractError("missing_retry_binding")
    for plan in (previous, current):
        if plan.get("schema") != _TRANSPORT_SCHEMA or plan.get("dispatch_authorized") is not False:
            raise UHPContractError("retry_plan_untrusted")
        if plan.get("method") != "POST" or plan.get("relative_path") != "/v1/responses":
            raise UHPContractError("retry_endpoint_untrusted")
        if plan.get("headers", {}).get("Idempotency-Key") != plan.get("idempotency_key"):
            raise UHPContractError("retry_header_mismatch")
    same_work = (
        previous["project_id"], previous["work_order_id"]
    ) == (
        current["project_id"], current["work_order_id"]
    )
    if not same_work:
        outcome = "DIFFERENT_WORK_ORDER_NOT_A_RETRY"
    elif any(previous[x] != current[x] for x in fields):
        outcome = "RETRY_BINDING_COLLISION_HOLD"
    elif last_state in ("UNKNOWN_OUTCOME", "IN_PROGRESS"):
        outcome = "EXTERNAL_IDEMPOTENCY_WITNESS_REQUIRED"
    elif last_state == "COMPLETED":
        outcome = "COMPLETED_NO_REPLAY"
    else:
        outcome = "NEW_DISPATCH_APPROVAL_REQUIRED"
    return {
        "schema": "codexstation.omega.uhp.retry-review.v0.1",
        "verdict": outcome,
        "retry_authorized": False,
        "dispatch_authorized": False,
        "canonical_authority_delta": "NONE",
    }
