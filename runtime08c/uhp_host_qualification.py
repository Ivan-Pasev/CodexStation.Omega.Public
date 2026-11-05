"""UHP Slice 06: operator qualification PLAN, not an executor or witness.

The plan is deliberately usable by a separated observer in a future trial,
but neither an agent's report nor an untrusted host-origin label constitutes
independent evidence. No file/network/process/credential/host operations.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Mapping
from runtime08c.uhp_adapter import UHPContractError

MATRIX_SCHEMA = "codexstation.omega.uhp.host-qualification-matrix.v0.1"
PLAN_SCHEMA = "codexstation.omega.uhp.host-pilot-plan.v0.1"
REPORT_SCHEMA = "codexstation.omega.uhp.host-pilot-report.v0.1"
REVIEW_SCHEMA = "codexstation.omega.uhp.host-pilot-review.v0.1"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
SOURCE = re.compile(r"sha256:[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
FIELDS = frozenset({
    "project_id", "work_order_id", "source_commit", "source_digest",
    "observer_host_id", "executor_host_id", "observer_principal_id",
    "executor_principal_id", "execution_scope",
})
REPORT_FIELDS = frozenset({
    "schema", "plan_digest", "project_id", "work_order_id",
    "source_commit", "source_digest", "observer_host_id",
    "executor_host_id", "observer_principal_id", "executor_principal_id",
    "probes",
})


def _hash_json(obj):
    try:
        b = json.dumps(obj, ensure_ascii=True, allow_nan=False,
                       sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError, OverflowError) as e:
        raise UHPContractError("qualification_not_json") from e
    if len(b) > 32768:
        raise UHPContractError("qualification_json_too_large")
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _identity(x, name):
    if not isinstance(x, str) or not ID.fullmatch(x):
        raise UHPContractError("invalid_" + name)
    return x


def _matrix(matrix):
    if not isinstance(matrix, Mapping) or set(matrix) != {
        "schema", "intent", "controls", "negative_probes",
    }:
        raise UHPContractError("invalid_qualification_matrix")
    if matrix["schema"] != MATRIX_SCHEMA or matrix["intent"] != "OWNER_MANUAL_RUN_ONLY":
        raise UHPContractError("matrix_may_self_dispatch")
    controls = matrix["controls"]
    probes = matrix["negative_probes"]
    if (not isinstance(controls, list) or len(controls) < 5
            or not isinstance(probes, list) or not 8 <= len(probes) <= 32):
        raise UHPContractError("incomplete_qualification_matrix")
    cids = []
    for c in controls:
        if not isinstance(c, Mapping) or set(c) != {"id", "requirement"}:
            raise UHPContractError("malformed_qualification_control")
        cids.append(_identity(c["id"], "control_id"))
        if not isinstance(c["requirement"], str) or not c["requirement"].strip():
            raise UHPContractError("invalid_control_requirement")
    if len(cids) != len(set(cids)):
        raise UHPContractError("duplicate_control_id")
    pids = []
    for p in probes:
        if not isinstance(p, Mapping) or set(p) != {"id", "purpose", "expected"}:
            raise UHPContractError("malformed_qualification_probe")
        pids.append(_identity(p["id"], "probe_id"))
        if (not isinstance(p["purpose"], str) or not p["purpose"].strip()
                or p["expected"] not in ("DENIED", "REJECTED", "NO_AUTO_RETRY", "MATCH")):
            raise UHPContractError("invalid_probe_requirement")
    if len(pids) != len(set(pids)):
        raise UHPContractError("duplicate_probe_id")
    if not {"DENIED", "REJECTED", "NO_AUTO_RETRY", "MATCH"}.issubset(
        {p["expected"] for p in probes}
    ):
        raise UHPContractError("missing_probe_categories")
    return _hash_json(dict(matrix))


def compile_host_pilot_plan(config: Mapping, matrix: Mapping):
    """Pure static plan with all external trust gates held."""
    digest = _matrix(matrix)
    if not isinstance(config, Mapping) or set(config) != FIELDS:
        raise UHPContractError("invalid_pilot_configuration")
    for k in FIELDS - {"source_commit", "source_digest", "execution_scope"}:
        _identity(config[k], k)
    if (not isinstance(config["source_commit"], str)
            or not COMMIT.fullmatch(config["source_commit"])):
        raise UHPContractError("invalid_source_commit")
    if (not isinstance(config["source_digest"], str)
            or not SOURCE.fullmatch(config["source_digest"])):
        raise UHPContractError("invalid_source_digest")
    if config["execution_scope"] != "DISPOSABLE_READ_ONLY_NO_PROVIDER":
        raise UHPContractError("pilot_scope_unqualified")
    if (config["observer_host_id"] == config["executor_host_id"]
            or config["observer_principal_id"] == config["executor_principal_id"]):
        raise UHPContractError("same_claimed_trust_boundary")
    result = {
        "schema": PLAN_SCHEMA, "matrix_digest": digest, "config": dict(config),
        "required_controls": [c["id"] for c in matrix["controls"]],
        "negative_probes": [{"id":p["id"], "expected":p["expected"]}
                            for p in matrix["negative_probes"]],
        "proof_capture_mode": "EXTERNAL_OBSERVER_REQUIRED",
        "operator_execute_approved": False,
        "live_run_performed": False,
        "host_identity_verified": False,
        "independent_observer_verified": False,
        "dispatch_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
    }
    result["plan_digest"] = _hash_json(result)
    return result


def assess_report(plan: Mapping, matrix: Mapping, report: Mapping,
                  legacy_host_witness: Mapping | None = None):
    """Inspect untrusted claims; even a complete report never becomes PASS.

    Independent capture, verified key registry, host identity and operator
    approvals are outside this API. No cryptographic self-approval path.
    """
    digest = _matrix(matrix)
    if not isinstance(plan, Mapping) or plan.get("schema") != PLAN_SCHEMA:
        raise UHPContractError("pilot_plan_invalid")
    if plan.get("matrix_digest") != digest:
        raise UHPContractError("pilot_matrix_binding_mismatch")
    if plan.get("dispatch_authorized") is not False or plan.get("promotion_authorized") is not False:
        raise UHPContractError("pilot_authority_smuggling")
    if plan.get("canonical_authority_delta") != "NONE":
        raise UHPContractError("pilot_authority_delta")
    signed = dict(plan)
    plan_hash = signed.pop("plan_digest", None)
    if plan_hash != _hash_json(signed):
        raise UHPContractError("pilot_plan_digest_inconsistent")
    if not isinstance(report, Mapping) or set(report) != REPORT_FIELDS:
        raise UHPContractError("pilot_report_invalid")
    if report["schema"] != REPORT_SCHEMA or report["plan_digest"] != plan_hash:
        raise UHPContractError("report_plan_binding_mismatch")
    cfg = plan.get("config", {})
    for k in ("project_id", "work_order_id", "source_commit", "source_digest",
              "observer_host_id", "executor_host_id",
              "observer_principal_id", "executor_principal_id"):
        if report.get(k) != cfg.get(k):
            raise UHPContractError("pilot_report_identity_mismatch_" + k)
    observed = report["probes"]
    if not isinstance(observed, list) or len(observed) > 32:
        raise UHPContractError("pilot_probe_report_invalid")
    items = {}
    for entry in observed:
        if not isinstance(entry, Mapping) or set(entry) != {"id", "observed", "evidence_ref"}:
            raise UHPContractError("malformed_probe_report")
        name = _identity(entry["id"], "reported_probe_id")
        if name in items:
            raise UHPContractError("duplicated_probe_report")
        if entry["observed"] not in ("DENIED", "REJECTED", "NO_AUTO_RETRY", "MATCH", "UNKNOWN", "ALLOWED"):
            raise UHPContractError("probe_outcome_invalid")
        ref = entry["evidence_ref"]
        if ref is not None:
            _identity(ref, "evidence_ref")
        items[name] = entry
    expected = {x["id"]: x["expected"] for x in plan["negative_probes"]}
    reasons = []
    if set(items) != set(expected):
        reasons.append("INCOMPLETE_OR_EXTRA_PROBE_REPORT")
    if any(items[k]["observed"] != expected[k] for k in set(items) & set(expected)):
        reasons.append("NEGATIVE_PROBE_NOT_DENIED_AS_REQUIRED")
    if any(items[k]["evidence_ref"] is None for k in set(items) & set(expected)):
        reasons.append("INDEPENDENT_PROOF_REFERENCE_MISSING")
    if legacy_host_witness is not None:
        if not isinstance(legacy_host_witness, Mapping):
            raise UHPContractError("invalid_legacy_host_witness")
        if legacy_host_witness.get("witness_origin") == "LIVE_HOST":
            reasons.append("LEGACY_LIVE_HOST_LABEL_NOT_IDENTITY_PROOF")
    return {
        "schema": REVIEW_SCHEMA,
        "verdict": "HOLD" if reasons else "CLAIMS_COMPLETE_INDEPENDENT_PROOF_REQUIRED",
        "reasons": sorted(set(reasons)),
        "plan_digest": plan_hash,
        "claimed_results_count": len(items),
        "independent_host_identity_verified": False,
        "independent_capture_verified": False,
        "technical_isolation_verified": False,
        "secret_custody_verified": False,
        "durable_replay_verified": False,
        "external_effects_verified": False,
        "live_run_performed_by_this_api": False,
        "dispatch_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
    }
