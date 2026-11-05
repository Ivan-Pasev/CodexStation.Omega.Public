"""Slice 08: classify single-runner container inspect + observed smoke outcome.

Pure validation only. A matching Docker inspect document and zero worker exit
are not independent host identity, tamper-resistant evidence or a two-host
qualification. This module does no I/O and grants no runtime authority.
"""
from __future__ import annotations
import re
from collections.abc import Mapping
from runtime08c.uhp_adapter import UHPContractError

SCHEMA = "codexstation.omega.uhp.ci-containment-review.v0.1"
SHA = re.compile(r"[0-9a-f]{64}\Z")


def assess_ci_containment(inspect, exit_code, source_before, source_after):
    """Assess supplied Docker inspect data; never release a live harness."""
    if not isinstance(inspect, Mapping):
        raise UHPContractError("ci_containment_inspect_not_object")
    if type(exit_code) is not int or not 0 <= exit_code <= 255:
        raise UHPContractError("ci_containment_exit_invalid")
    for digest in (source_before, source_after):
        if not isinstance(digest, str) or SHA.fullmatch(digest) is None:
            raise UHPContractError("ci_containment_source_hash_invalid")

    hc = inspect.get("HostConfig")
    cfg = inspect.get("Config")
    state = inspect.get("State")
    mounts = inspect.get("Mounts")
    if not isinstance(hc, Mapping) or not isinstance(cfg, Mapping) or not isinstance(state, Mapping):
        raise UHPContractError("ci_containment_missing_inspection_fields")
    if not isinstance(mounts, list) or len(mounts) > 16:
        raise UHPContractError("ci_containment_mounts_malformed")
    reasons = []
    if hc.get("NetworkMode") != "none":
        reasons.append("NETWORK_NOT_DISABLED")
    if hc.get("ReadonlyRootfs") is not True:
        reasons.append("ROOT_FILESYSTEM_NOT_READONLY")
    drops = hc.get("CapDrop")
    if not isinstance(drops, list) or "ALL" not in [str(s).upper() for s in drops]:
        reasons.append("CAPABILITIES_NOT_DROPPED")
    opts = hc.get("SecurityOpt")
    if not isinstance(opts, list) or "no-new-privileges" not in opts:
        reasons.append("PRIVILEGE_ESCALATION_NOT_FORBIDDEN")
    if hc.get("Privileged") is not False:
        reasons.append("PRIVILEGED_CONTAINER")
    if cfg.get("User") != "65534:65534":
        reasons.append("USER_NOT_EXPLICITLY_NONROOT")
    if cfg.get("Entrypoint") != ["/worker"]:
        reasons.append("UNEXPECTED_EXECUTABLE")
    if type(hc.get("Memory")) is not int or hc["Memory"] < 67108864:
        reasons.append("MEMORY_LIMIT_MISSING")
    if type(hc.get("PidsLimit")) is not int or not 1 <= hc["PidsLimit"] <= 64:
        reasons.append("PID_LIMIT_MISSING")
    if type(hc.get("NanoCpus")) is not int or not 0 < hc["NanoCpus"] <= 1000000000:
        reasons.append("CPU_LIMIT_MISSING")
    if hc.get("PidMode") in ("host", "container:host"):
        reasons.append("HOST_PID_NAMESPACE_PRESENT")
    if hc.get("IpcMode") == "host":
        reasons.append("HOST_IPC_NAMESPACE_PRESENT")
    if hc.get("Devices"):
        reasons.append("EXTRA_DEVICES_PRESENT")
    binds = [m for m in mounts if isinstance(m, Mapping)]
    if len(binds) != 1 or len(binds) != len(mounts):
        reasons.append("UNEXPECTED_MOUNT_COUNT")
    else:
        mount = binds[0]
        if (mount.get("Type") != "bind" or mount.get("Destination") != "/source"
                or mount.get("RW") is not False):
            reasons.append("SOURCE_MOUNT_NOT_READONLY")
    if state.get("ExitCode") != exit_code or state.get("Running") is not False:
        reasons.append("EXIT_CODE_NOT_INDEPENDENTLY_MATCHED")
    if exit_code != 0:
        reasons.append("NEGATIVE_PROBE_WORKER_FAILED")
    if source_before != source_after:
        reasons.append("SOURCE_SNAPSHOT_CHANGED")
    return {
        "schema": SCHEMA,
        "verdict": "HOLD" if reasons else "SINGLE_RUNNER_SMOKE_SHAPE_ONLY",
        "reasons": sorted(set(reasons)),
        "source_digest_before": source_before,
        "source_digest_after": source_after,
        "source_snapshot_unchanged": source_before == source_after,
        "inspect_shape_consistent": not reasons,
        "single_runner_probe_executed": True,
        "independent_host_verified": False,
        "separate_observer_verified": False,
        "technical_isolation_independently_verified": False,
        "network_egress_independently_verified": False,
        "source_capture_provenance_verified": False,
        "durable_replay_verified": False,
        "external_effects_verified": False,
        "real_uhp_task_executed": False,
        "dispatch_authorized": False,
        "retry_authorized": False,
        "promotion_authorized": False,
        "canonical_authority_delta": "NONE",
    }
