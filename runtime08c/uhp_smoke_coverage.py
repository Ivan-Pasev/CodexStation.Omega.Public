"""Bridge a single-runner smoke to PARTIAL research coverage, never authority."""
import hashlib
import json
import re
from collections.abc import Mapping
from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_ci_containment import SCHEMA as SMOKE_SCHEMA
from runtime08c.uhp_host_qualification import MATRIX_SCHEMA

SCHEMA = "codexstation.omega.uhp.ci-coverage-bridge.v0.1"
HEXDIGEST = re.compile(r"[0-9a-f]{64}\Z")
PARTIAL = {
    "N01": "synthetic source write attempted",
    "N03": "fixed TCP denied and Docker network-mode none claimed",
    "N06": "Docker socket read denied only; not full escalation test",
    "N12": "synthetic fixture pre/post hash equality on one runner",
}
DENIED_AUTHORITY = (
    "dispatch_authorized", "retry_authorized", "promotion_authorized",
    "independent_host_verified", "separate_observer_verified",
    "technical_isolation_independently_verified",
    "network_egress_independently_verified",
    "source_capture_provenance_verified", "durable_replay_verified",
    "external_effects_verified", "real_uhp_task_executed",
)


def _hash_record(data):
    try:
        raw = json.dumps(data, allow_nan=False, ensure_ascii=True,
                         sort_keys=True, separators=(",", ":")).encode("ascii")
    except (TypeError, ValueError, OverflowError, RecursionError) as e:
        raise UHPContractError("bridge_invalid_json") from e
    if len(raw) > 32768:
        raise UHPContractError("bridge_unbounded_json")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def reconcile_ci_smoke(matrix: Mapping, smoke: Mapping):
    """Classify only potential subset coverage. Self-reports cannot certify hosts."""
    if (not isinstance(matrix, Mapping) or matrix.get("schema") != MATRIX_SCHEMA
            or matrix.get("intent") != "OWNER_MANUAL_RUN_ONLY"):
        raise UHPContractError("bridge_matrix_invalid")
    probes = matrix.get("negative_probes")
    if not isinstance(probes, list) or len(probes) != 12:
        raise UHPContractError("bridge_probe_inventory_invalid")
    expectations = {}
    for item in probes:
        if (not isinstance(item, Mapping)
                or set(item) != {"id", "purpose", "expected"}
                or not isinstance(item["id"], str)
                or item["id"] in expectations):
            raise UHPContractError("bridge_probe_invalid")
        expectations[item["id"]] = item["expected"]
    if set(expectations) != {"N%02d" % k for k in range(1, 13)}:
        raise UHPContractError("bridge_probe_id_set_invalid")
    if any(expectations[key] != val for key, val in (
        ("N01", "DENIED"), ("N03", "DENIED"),
        ("N06", "DENIED"), ("N12", "MATCH")
    )):
        raise UHPContractError("bridge_matrix_expectations_changed")

    if not isinstance(smoke, Mapping) or smoke.get("schema") != SMOKE_SCHEMA:
        raise UHPContractError("bridge_smoke_schema_invalid")
    for field in DENIED_AUTHORITY:
        if smoke.get(field) is not False:
            raise UHPContractError("bridge_authority_smuggling_" + field)
    if smoke.get("canonical_authority_delta") != "NONE":
        raise UHPContractError("bridge_authority_delta")
    if smoke.get("single_runner_probe_executed") is not True:
        raise UHPContractError("bridge_probe_unexecuted")
    for field in ("source_digest_before", "source_digest_after"):
        if (not isinstance(smoke.get(field), str)
                or not HEXDIGEST.fullmatch(smoke[field])):
            raise UHPContractError("bridge_source_digest_invalid")
    expected_equal = smoke["source_digest_before"] == smoke["source_digest_after"]
    if smoke.get("source_snapshot_unchanged") is not expected_equal:
        raise UHPContractError("bridge_source_claim_inconsistent")
    if (not isinstance(smoke.get("reasons"), list)
            or len(smoke["reasons"]) > 32
            or any(not isinstance(v, str) or len(v) > 128
                   for v in smoke["reasons"])):
        raise UHPContractError("bridge_reasons_invalid")
    if smoke.get("verdict") not in ("HOLD", "SINGLE_RUNNER_SMOKE_SHAPE_ONLY"):
        raise UHPContractError("bridge_verdict_invalid")
    clean = (smoke["verdict"] == "SINGLE_RUNNER_SMOKE_SHAPE_ONLY"
             and not smoke["reasons"]
             and smoke.get("inspect_shape_consistent") is True
             and expected_equal)
    subset = [{"probe_id": p, "description": PARTIAL[p],
               "status": "SINGLE_RUNNER_UNATTESTED"}
              for p in sorted(PARTIAL)] if clean else []
    return {
        "schema": SCHEMA,
        "verdict": "PARTIAL_SINGLE_RUNNER_RESEARCH_ONLY" if clean else "HOLD",
        "smoke_receipt_digest": _hash_record(dict(smoke)),
        "matrix_digest": _hash_record(dict(matrix)),
        "partially_exercised": subset,
        "not_exercised": sorted(set(expectations) - {v["probe_id"] for v in subset}),
        "externally_qualified_probe_ids": [],
        "full_matrix_qualified": False,
        "independent_observer_verified": False,
        "two_host_qualification_verified": False,
        "durable_replay_verified": False,
        "actual_uhp_task_executed": False,
        "dispatch_authorized": False,
        "retry_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
    }
