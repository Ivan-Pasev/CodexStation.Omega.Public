"""Offline UHP v2026-10-19 proposal compiler for CodexStation Omega.
Never dispatches, grants permissions, accesses the filesystem, or changes canon.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Mapping

UHP_VERSION = "2026-10-19"
SCHEMA = "codexstation.omega.uhp.work-order.v0.1"
STATUSES = {"in_progress", "completed", "failed", "incomplete", "cancelled"}
FIELDS = {"schema", "work_order_id", "project_id", "input", "harness_id",
          "model", "source_digest", "effect_class", "max_step",
          "timeout_seconds", "environment_id", "hard_tool_restrictions"}

class UHPContractError(ValueError):
    """Mismatch must HOLD rather than dispatch."""

def _text(value, name, limit=8192):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise UHPContractError("invalid_" + name)
    return value

def _sha(value):
    b = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                   separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def compile_task(order: Mapping, capabilities: Mapping):
    """Compile an UNAUTHORIZED proposal, not an enforced read-only operation.

    Source digest and harness inventory here are unverified caller assertions.
    This module has no transport and no capability to authorize dispatch.
    """
    if not isinstance(order, Mapping) or not isinstance(capabilities, Mapping):
        raise UHPContractError("invalid_input")
    if set(order) - FIELDS:
        raise UHPContractError("unrecognized_order_fields")
    if order.get("schema") != SCHEMA:
        raise UHPContractError("unsupported_schema")
    if order.get("effect_class") != "READ_ONLY":
        raise UHPContractError("effectful_task_forbidden")
    if order.get("hard_tool_restrictions") is not False:
        raise UHPContractError("tool_enforcement_unqualified")
    for name in ("work_order_id", "project_id", "harness_id", "model"):
        _text(order.get(name), name, 128)
    _text(order.get("input"), "input")
    sd = _text(order.get("source_digest"), "source_digest", 71)
    if re.fullmatch(r"sha256:[0-9a-f]{64}", sd) is None:
        raise UHPContractError("unbound_source")
    for name, lo, hi in (("max_step", 1, 8), ("timeout_seconds", 1, 300)):
        v = order.get(name)
        if type(v) is not int or not lo <= v <= hi:
            raise UHPContractError("invalid_" + name)
    if capabilities.get("version") != UHP_VERSION:
        raise UHPContractError("uhp_version_mismatch")
    harnesses = capabilities.get("harness_ids")
    if not isinstance(harnesses, list) or order["harness_id"] not in harnesses:
        raise UHPContractError("unobserved_harness")
    metadata = {"harness_id": order["harness_id"]}
    if "environment_id" in order:
        _text(order["environment_id"], "environment_id", 128)
        if capabilities.get("environments") is not True:
            raise UHPContractError("environment_capability_missing")
        # 0.38.2 implementation and environments.md use metadata.environment.
        # tasks.md instead shows a top-level environment. Conformance is OPEN.
        metadata["environment"] = order["environment_id"]
    req = {"input": order["input"], "model": order["model"],
           "metadata": metadata, "stream": False, "store": False,
           "max_step": order["max_step"],
           "timeout_seconds": order["timeout_seconds"]}
    contract = {"schema": "codexstation.omega.uhp.proposal.v0.1",
                "protocol_version": UHP_VERSION, "work_order_id": order["work_order_id"],
                "project_id": order["project_id"], "source_digest": sd,
                "work_order_sha256": _sha(dict(order)), "request_sha256": _sha(req),
                "expected_model": order["model"],
                "expected_harness_id": order["harness_id"],
                "expected_environment": metadata.get("environment"),
                "dispatch_authorized": False, "canonical_authority_delta": "NONE",
                "effect_confirmation": "NOT_OBSERVED",
                "capability_claim": "UNATTESTED"}
    return req, contract


def analyze_discovery(discovery: Mapping):
    """Static UHP discovery syntax check, NEVER endpoint or identity attestation.

    GET /v1/uhp is intentionally unauthenticated by the UHP specification.
    Live server identity, principal scope and harnesses require other evidence.
    """
    if not isinstance(discovery, Mapping):
        raise UHPContractError("invalid_discovery")
    problems = []
    if discovery.get("object") != "uhp.discovery" or discovery.get("protocol") != "uhp":
        problems.append("NOT_UHP_DISCOVERY")
    versions = discovery.get("versions")
    if (not isinstance(versions, list) or not versions
            or not all(isinstance(v, str) for v in versions)):
        problems.append("INVALID_VERSIONS")
        versions = []
    if UHP_VERSION not in versions:
        problems.append("PINNED_VERSION_MISSING")
    if discovery.get("default_version") not in versions:
        problems.append("INVALID_DEFAULT_VERSION")
    cls = discovery.get("conformance_class")
    if cls not in ("core", "extended", "full"):
        problems.append("INVALID_CONFORMANCE_CLASS")
    capabilities = discovery.get("capabilities")
    if not isinstance(capabilities, Mapping):
        problems.append("INVALID_CAPABILITIES")
        capabilities = {}
    elif not all(isinstance(k, str) and type(v) is bool
                 for k, v in capabilities.items()):
        problems.append("NONBOOLEAN_CAPABILITY")
    if cls in ("extended", "full") and not all(
        capabilities.get(k) is True for k in
        ("files_input", "files_output", "session_listing")
    ):
        problems.append("CLASS_CAPABILITY_CONTRADICTION")
    if capabilities.get("plugins") is True and not (
        isinstance(discovery.get("plugin_schemas"), list)
        and bool(discovery["plugin_schemas"])
        and all(isinstance(u, str) and u.startswith("https://")
                for u in discovery["plugin_schemas"])
    ):
        problems.append("PLUGIN_SCHEMA_DECLARATION_MISSING")
    return {
        "schema": "codexstation.omega.uhp.discovery-review.v0.1",
        "pinned_protocol": UHP_VERSION,
        "syntactic_compatibility": "PASS" if not problems else "HOLD",
        "issues": problems,
        "server_identity_attested": False,
        "principal_scope_attested": False,
        "configured_harness_attested": False,
        "runtime_security_qualified": False,
        "dispatch_authorized": False,
        "canonical_authority_delta": "NONE",
    }


def _response_envelope_issues(response):
    """Validate protocol-required envelope fields before claiming task completion."""
    problems = []
    if response.get("object") != "response":
        problems.append("RESPONSE_OBJECT_INVALID")
    if type(response.get("created_at")) is not int or response["created_at"] < 0:
        problems.append("RESPONSE_TIMESTAMP_INVALID")
    if not isinstance(response.get("output"), list):
        problems.append("RESPONSE_OUTPUT_INVALID")
    if "usage" not in response or (
        response["usage"] is not None and not isinstance(response["usage"], Mapping)
    ):
        problems.append("RESPONSE_USAGE_INVALID")
    if "previous_response_id" not in response or (
        response["previous_response_id"] is not None
        and not isinstance(response["previous_response_id"], str)
    ):
        problems.append("PREVIOUS_RESPONSE_INVALID")
    if response.get("store") is not False:
        problems.append("STORE_CONTRACT_MISMATCH")
    md = response.get("metadata", {})
    if not isinstance(md.get("session_id"), str) or not md["session_id"].strip():
        problems.append("SESSION_ID_MISSING")
    status = response.get("status")
    err = response.get("error", "MISSING")
    incomplete = response.get("incomplete_details", "MISSING")
    if err == "MISSING" or (
        status == "failed" and not isinstance(err, Mapping)
    ) or (status != "failed" and err is not None):
        problems.append("ERROR_STATUS_INCONSISTENT")
    if incomplete == "MISSING" or (
        status == "incomplete" and not (
            isinstance(incomplete, Mapping)
            and isinstance(incomplete.get("reason"), str)
            and incomplete.get("reason")
        )
    ) or (status != "incomplete" and incomplete is not None):
        problems.append("INCOMPLETE_STATUS_INCONSISTENT")
    return problems


def _bounded_response_sha256(response):
    """Refuse to hash oversized or non-JSON response envelopes."""
    try:
        data = json.dumps(dict(response), sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError):
        return None
    if len(data) > 262144:
        return None
    return hashlib.sha256(data).hexdigest()

def normalize_response(contract: Mapping, response: Mapping):
    """Normalize UHP observations; success does not establish external effects."""
    if not isinstance(contract, Mapping) or not isinstance(response, Mapping):
        raise UHPContractError("invalid_response")
    if contract.get("dispatch_authorized") is not False:
        raise UHPContractError("authorization_smuggling")
    if contract.get("protocol_version") != UHP_VERSION:
        raise UHPContractError("version_mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", str(contract.get("request_sha256", ""))):
        raise UHPContractError("unbound_request")
    st = response.get("status")
    if not isinstance(st, str) or st not in STATUSES:
        raise UHPContractError("unknown_task_status")
    md = response.get("metadata")
    if not isinstance(md, Mapping):
        raise UHPContractError("missing_response_metadata")
    _text(response.get("id"), "response_id", 256)
    holds = _response_envelope_issues(response)
    response_digest = _bounded_response_sha256(response)
    if response_digest is None:
        holds.append("UNBOUNDED_OR_NON_JSON_RESPONSE")
    if md.get("harness_id") != contract.get("expected_harness_id"):
        holds.append("HARNESS_MISMATCH")
    if response.get("model") != contract.get("expected_model") or md.get("model_fallback") is True or (
        "requested_model" in md and md.get("requested_model") != contract.get("expected_model")
    ):
        holds.append("MODEL_SUBSTITUTION")
    env = contract.get("expected_environment")
    if env is not None and md.get("environment") != env:
        holds.append("ENVIRONMENT_MISMATCH")
    ignored = md.get("ignored_fields", [])
    if not isinstance(ignored, list) or not all(isinstance(v, str) for v in ignored):
        holds.append("INVALID_IGNORED_FIELDS")
    elif {"input", "model", "metadata", "stream", "max_step", "timeout_seconds", "store"} & set(ignored):
        holds.append("IGNORED_CONTRACT_FIELD")
    verdict = ("HOLD" if holds else
               "TASK_COMPLETED_EFFECT_UNVERIFIED" if st == "completed" else
               {"in_progress": "IN_PROGRESS", "failed": "FAILED_NO_PROMOTION",
                "incomplete": "INCOMPLETE_NO_PROMOTION",
                "cancelled": "CANCELLED_NO_PROMOTION"}[st])
    return {"schema": "codexstation.omega.uhp.execution-observation.v0.1",
            "work_order_id": contract.get("work_order_id"),
            "response_id": response["id"], "response_sha256": response_digest,
            "uhp_status": st, "verdict": verdict, "hold_reasons": holds,
            "evidence_status": "UNVERIFIED",
            "read_only_enforcement": "NOT_ATTESTED",
            "source_content_verified": False,
            "server_identity_attested": False,
            "effect_confirmation": ("UNKNOWN_OUTCOME" if st == "completed" else "NOT_OBSERVED"),
            "dispatch_authorized": False, "promotion_authorized": False,
            "canonical_authority_delta": "NONE"}
