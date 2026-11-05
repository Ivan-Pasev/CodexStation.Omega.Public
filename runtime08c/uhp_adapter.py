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
    """Compile an UNAUTHORIZED request proposal from untrusted capability data."""
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
    if st not in STATUSES:
        raise UHPContractError("unknown_task_status")
    md = response.get("metadata")
    if not isinstance(md, Mapping):
        raise UHPContractError("missing_response_metadata")
    _text(response.get("id"), "response_id", 256)
    holds = []
    if md.get("harness_id") != contract.get("expected_harness_id"):
        holds.append("HARNESS_MISMATCH")
    if response.get("model") != contract.get("expected_model") or md.get("model_fallback") is True:
        holds.append("MODEL_SUBSTITUTION")
    env = contract.get("expected_environment")
    if env is not None and md.get("environment") != env:
        holds.append("ENVIRONMENT_MISMATCH")
    ignored = md.get("ignored_fields", [])
    if not isinstance(ignored, list) or not all(isinstance(v, str) for v in ignored):
        holds.append("INVALID_IGNORED_FIELDS")
    elif {"model", "metadata", "max_step", "timeout_seconds", "store"} & set(ignored):
        holds.append("IGNORED_CONTRACT_FIELD")
    verdict = ("HOLD" if holds else
               "TASK_COMPLETED_EFFECT_UNVERIFIED" if st == "completed" else
               {"in_progress": "IN_PROGRESS", "failed": "FAILED_NO_PROMOTION",
                "incomplete": "INCOMPLETE_NO_PROMOTION",
                "cancelled": "CANCELLED_NO_PROMOTION"}[st])
    return {"schema": "codexstation.omega.uhp.execution-observation.v0.1",
            "work_order_id": contract.get("work_order_id"),
            "response_id": response["id"], "response_sha256": _sha(dict(response)),
            "uhp_status": st, "verdict": verdict, "hold_reasons": holds,
            "evidence_status": "UNVERIFIED",
            "effect_confirmation": ("UNKNOWN_OUTCOME" if st == "completed" else "NOT_OBSERVED"),
            "dispatch_authorized": False, "promotion_authorized": False,
            "canonical_authority_delta": "NONE"}
