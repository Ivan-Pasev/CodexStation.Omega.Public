"""CodexStation Ω Constitutional Reference Runtime v0.8c.

Pure-stdlib, deterministic reference implementation of the public 0.8b ABI.
It performs no external side effects by default.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Callable, Iterable

AUTHORITY_LEVELS = {f"A{i}": i for i in range(6)}
TERMINAL_FAILURES = {"REJECT", "BLOCK"}
UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(domain: str, value: Any) -> dict[str, str]:
    return {
        "algorithm": "sha256",
        "value": hashlib.sha256(canonical_bytes({"domain": domain, "value": value})).hexdigest(),
        "domain": domain,
    }


def _state_material(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "state_id": state["state_id"],
        "project_id": state["project_id"],
        "revision": state["revision"],
        "payload": state.get("payload", {}),
        "grants": state.get("grants", []),
        "provenance_refs": state.get("provenance_refs", []),
        "conflicts": state.get("conflicts", []),
        "health": state.get("health", "HEALTHY"),
    }


def make_state(
    *,
    project_id: str,
    state_id: str = "state:0",
    revision: int = 0,
    payload: dict[str, Any] | None = None,
    grants: list[dict[str, Any]] | None = None,
    provenance_refs: list[str] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
    health: str = "HEALTHY",
) -> dict[str, Any]:
    state = {
        "state_id": state_id,
        "project_id": project_id,
        "revision": revision,
        "payload": copy.deepcopy(payload or {}),
        "grants": copy.deepcopy(grants or []),
        "provenance_refs": list(provenance_refs or []),
        "conflicts": copy.deepcopy(conflicts or []),
        "health": health,
    }
    state["digest"] = digest("canonical-state", _state_material(state))
    return state


def verify_state(state: dict[str, Any]) -> bool:
    return state.get("digest") == digest("canonical-state", _state_material(state))


def plan_digest(transition: dict[str, Any]) -> dict[str, str]:
    return digest("authorized-plan", transition.get("operations", []))


def _grant_level(grants: Iterable[dict[str, Any]], principal_id: str) -> int:
    levels = [
        AUTHORITY_LEVELS.get(g.get("level"), -1)
        for g in grants
        if g.get("principal_id") == principal_id and not g.get("revoked", False)
    ]
    return max(levels, default=-1)


def _grant_rights(grants: Iterable[dict[str, Any]], principal_id: str) -> set[str]:
    out: set[str] = set()
    for grant in grants:
        if grant.get("principal_id") == principal_id and not grant.get("revoked", False):
            out.update(grant.get("rights", []))
    return out


def authority_check(state: dict[str, Any], transition: dict[str, Any]) -> dict[str, Any]:
    principal = transition["proposer_principal_id"]
    required = transition.get("required_authority", [])
    level = _grant_level(state.get("grants", []), principal)
    rights = _grant_rights(state.get("grants", []), principal)
    missing: list[str] = []
    for req in required:
        if req in AUTHORITY_LEVELS:
            if level < AUTHORITY_LEVELS[req]:
                missing.append(req)
        elif req not in rights:
            missing.append(req)
    return {
        "status": "PASS" if not missing else "FAIL",
        "principal_id": principal,
        "predecessor_level": level,
        "missing": missing,
    }


def invariant_check(
    transition: dict[str, Any], invariant_results: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    by_id = {x["invariant_id"]: x for x in invariant_results}
    failures: list[str] = []
    unresolved: list[str] = []
    for invariant_id in transition.get("protected_invariants", []):
        result = by_id.get(invariant_id)
        if result is None or result.get("status") == "UNRESOLVED":
            unresolved.append(invariant_id)
        elif result.get("status") != "PASS":
            failures.append(invariant_id)
    status = "PASS" if not failures and not unresolved else "FAIL"
    return {"status": status, "failures": failures, "unresolved": unresolved}


def _authority_escalation_attempt(
    state: dict[str, Any], transition: dict[str, Any]
) -> list[dict[str, Any]]:
    if transition.get("kind") == "GOVERNANCE":
        return []
    current = {
        (g.get("principal_id"), g.get("grant_id")): AUTHORITY_LEVELS.get(g.get("level"), -1)
        for g in state.get("grants", [])
    }
    violations = []
    for op in transition.get("operations", []):
        if op.get("op") != "GRANT":
            continue
        grant = op.get("grant", {})
        key = (grant.get("principal_id"), grant.get("grant_id"))
        old = current.get(key, -1)
        new = AUTHORITY_LEVELS.get(grant.get("level"), -1)
        if new > old:
            violations.append({"grant": grant, "previous_level": old, "new_level": new})
    return violations


def admit_transition(
    state: dict[str, Any],
    transition: dict[str, Any],
    *,
    semantic_decision: dict[str, Any],
    invariant_results: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    reasons: list[str] = []
    if not verify_state(state):
        reasons.append("CURRENT_STATE_DIGEST_INVALID")
    if transition.get("project_id") != state.get("project_id"):
        reasons.append("PROJECT_MISMATCH")
    if transition.get("parent_state_digest") != state.get("digest"):
        reasons.append("STALE_OR_FOREIGN_PARENT")
    if semantic_decision.get("status") not in {"ALLOW", "PASS"}:
        reasons.append("SEMANTIC_DECISION_NOT_ALLOW")
    invariant = invariant_check(transition, invariant_results)
    if invariant["status"] != "PASS":
        reasons.append("PROTECTED_INVARIANT_NOT_PASS")
    authority = authority_check(state, transition)
    if authority["status"] != "PASS":
        reasons.append("INSUFFICIENT_PREDECESSOR_AUTHORITY")
    if transition.get("authorized_plan_digest") not in (None, plan_digest(transition)):
        reasons.append("AUTHORIZED_PLAN_BINDING_MISMATCH")
    if _authority_escalation_attempt(state, transition):
        reasons.append("NON_GOVERNANCE_AUTHORITY_ESCALATION")
    return {
        "status": "ADMIT" if not reasons else "HOLD",
        "reasons": reasons,
        "semantic": semantic_decision,
        "invariants": invariant,
        "authorization": authority,
    }


def _apply_local_operation(payload: dict[str, Any], op: dict[str, Any]) -> None:
    kind = op.get("op")
    key = op.get("key")
    if kind == "SET":
        if not isinstance(key, str) or not key:
            raise ValueError("SET requires non-empty key")
        payload[key] = copy.deepcopy(op.get("value"))
    elif kind == "DELETE":
        if not isinstance(key, str) or not key:
            raise ValueError("DELETE requires non-empty key")
        payload.pop(key, None)
    elif kind == "ASSERT":
        if payload.get(key) != op.get("equals"):
            raise ValueError("ASSERT failed")
    elif kind == "GRANT":
        return
    elif kind == "EFFECT":
        return
    else:
        raise ValueError(f"unsupported operation: {kind}")


def execute_transition(
    state: dict[str, Any],
    transition: dict[str, Any],
    *,
    semantic_decision: dict[str, Any],
    invariant_results: Iterable[dict[str, Any]],
    effect_executor: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    admission = admit_transition(
        state,
        transition,
        semantic_decision=semantic_decision,
        invariant_results=invariant_results,
    )
    before = state["digest"]
    base_receipt = {
        "receipt_id": digest(
            "receipt-id",
            {
                "transition_id": transition["transition_id"],
                "before": before,
            },
        )["value"],
        "receipt_type": "TRANSITION",
        "subject_id": transition["transition_id"],
        "before_digest": before,
        "authority_refs": transition.get("required_authority", []),
        "invariant_results": list(invariant_results),
        "evidence_refs": transition.get("evidence_refs", []),
        "source_profile": transition.get("source_profile", "OMEGA_08C"),
    }

    if admission["status"] != "ADMIT":
        receipt = {
            **base_receipt,
            "outcome": "HOLD",
            "after_digest": None,
            "decision_vector": {
                "semantic": semantic_decision,
                "admission": admission,
                "authorization": admission["authorization"],
                "execution": None,
                "closure": {"status": "HOLD"},
            },
        }
        return {"status": "HOLD", "state": state, "receipt": receipt, "event": None}

    next_payload = copy.deepcopy(state.get("payload", {}))
    next_grants = copy.deepcopy(state.get("grants", []))
    effect_receipts: list[dict[str, Any]] = []

    try:
        for op in transition.get("operations", []):
            if op.get("op") == "EFFECT":
                if effect_executor is None:
                    effect_receipts.append({"status": UNKNOWN_OUTCOME, "operation": op})
                    continue
                result = effect_executor(copy.deepcopy(op))
                if result.get("status") not in {"PASS", "FAIL", UNKNOWN_OUTCOME}:
                    result = {**result, "status": UNKNOWN_OUTCOME}
                effect_receipts.append(result)
                continue
            if op.get("op") == "GRANT":
                if transition.get("kind") != "GOVERNANCE":
                    raise ValueError("grant mutation outside governance")
                next_grants.append(copy.deepcopy(op["grant"]))
                continue
            _apply_local_operation(next_payload, op)
    except Exception as exc:
        receipt = {
            **base_receipt,
            "outcome": "FAIL",
            "after_digest": None,
            "error": type(exc).__name__,
            "decision_vector": {
                "semantic": semantic_decision,
                "admission": admission,
                "authorization": admission["authorization"],
                "execution": {"status": "FAIL"},
                "closure": {"status": "HOLD"},
            },
        }
        return {"status": "FAIL", "state": state, "receipt": receipt, "event": None}

    if any(x.get("status") == UNKNOWN_OUTCOME for x in effect_receipts):
        receipt = {
            **base_receipt,
            "outcome": UNKNOWN_OUTCOME,
            "after_digest": None,
            "effect_receipts": effect_receipts,
            "decision_vector": {
                "semantic": semantic_decision,
                "admission": admission,
                "authorization": admission["authorization"],
                "execution": {"status": UNKNOWN_OUTCOME},
                "closure": {"status": "HOLD"},
            },
        }
        return {"status": UNKNOWN_OUTCOME, "state": state, "receipt": receipt, "event": None}

    if any(x.get("status") == "FAIL" for x in effect_receipts):
        receipt = {
            **base_receipt,
            "outcome": "FAIL",
            "after_digest": None,
            "effect_receipts": effect_receipts,
            "decision_vector": {
                "semantic": semantic_decision,
                "admission": admission,
                "authorization": admission["authorization"],
                "execution": {"status": "FAIL"},
                "closure": {"status": "HOLD"},
            },
        }
        return {"status": "FAIL", "state": state, "receipt": receipt, "event": None}

    successor = make_state(
        project_id=state["project_id"],
        state_id=f"{state['project_id']}:state:{state['revision'] + 1}",
        revision=state["revision"] + 1,
        payload=next_payload,
        grants=next_grants,
        provenance_refs=state.get("provenance_refs", [])
        + [f"transition:{transition['transition_id']}"],
        conflicts=state.get("conflicts", []),
        health=state.get("health", "HEALTHY"),
    )
    receipt = {
        **base_receipt,
        "outcome": "PASS",
        "after_digest": successor["digest"],
        "effect_receipts": effect_receipts,
        "decision_vector": {
            "semantic": semantic_decision,
            "admission": admission,
            "authorization": admission["authorization"],
            "execution": {"status": "PASS"},
            "closure": {"status": "CLOSED"},
        },
    }
    event = {
        "event_id": digest(
            "event-id",
            {
                "transition_id": transition["transition_id"],
                "before": before,
                "after": successor["digest"],
            },
        )["value"],
        "sequence": successor["revision"],
        "event_type": "TRANSITION_APPLIED",
        "subject_ref": transition["transition_id"],
        "before_digest": before,
        "after_digest": successor["digest"],
        "receipt_ref": receipt["receipt_id"],
    }
    return {"status": "PASS", "state": successor, "receipt": receipt, "event": event}


def make_conflict(
    *,
    conflict_id: str,
    conflict_type: str,
    participants: list[str],
    evidence_refs: list[str] | None = None,
    severity: str = "MEDIUM",
) -> dict[str, Any]:
    return {
        "conflict_id": conflict_id,
        "conflict_type": conflict_type,
        "participants": list(participants),
        "status": "OPEN",
        "evidence_refs": list(evidence_refs or []),
        "severity": severity,
    }


def fold_events(initial_state: dict[str, Any], transitions: list[dict[str, Any]]) -> dict[str, Any]:
    state = copy.deepcopy(initial_state)
    receipts = []
    events = []
    for item in transitions:
        result = execute_transition(
            state,
            item["transition"],
            semantic_decision=item["semantic_decision"],
            invariant_results=item["invariant_results"],
            effect_executor=item.get("effect_executor"),
        )
        receipts.append(result["receipt"])
        if result["event"] is not None:
            events.append(result["event"])
        if result["status"] != "PASS":
            return {
                "status": result["status"],
                "state": state,
                "receipts": receipts,
                "events": events,
            }
        state = result["state"]
    return {"status": "PASS", "state": state, "receipts": receipts, "events": events}


def recovery_check(
    source_state: dict[str, Any],
    target_state: dict[str, Any],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    objects_verified = verify_state(source_state) and verify_state(target_state)
    receipt_verified = (
        receipt.get("before_digest") == source_state.get("digest")
        and receipt.get("after_digest") == target_state.get("digest")
        and receipt.get("outcome") == "PASS"
    )
    return {
        "recovery_id": digest(
            "recovery",
            {
                "source": source_state.get("digest"),
                "target": target_state.get("digest"),
                "receipt": receipt.get("receipt_id"),
            },
        )["value"],
        "source_state_ref": source_state["state_id"],
        "target_state_ref": target_state["state_id"],
        "objects_verified": objects_verified,
        "receipt_verified": receipt_verified,
        "residuals": [],
        "status": "RECOVERABLE" if objects_verified and receipt_verified else "QUARANTINE",
    }


def compile_archetonic_plate(
    *,
    plate_id: str,
    project_id: str,
    state: dict[str, Any],
    principal_id: str,
    operations: list[dict[str, Any]],
    required_authority: list[str],
    protected_invariants: list[str],
    evidence_refs: list[str] | None = None,
    kind: str = "OPERATIONAL",
) -> dict[str, Any]:
    transition = {
        "transition_id": f"{plate_id}:transition",
        "project_id": project_id,
        "parent_state_digest": state["digest"],
        "proposer_principal_id": principal_id,
        "kind": kind,
        "operations": copy.deepcopy(operations),
        "required_authority": list(required_authority),
        "protected_invariants": list(protected_invariants),
        "verification_plan": [],
        "reversibility": "REVERSIBLE",
        "evidence_refs": list(evidence_refs or []),
        "source_profile": "ARCHETONIC_PLATE_08C",
    }
    transition["authorized_plan_digest"] = plan_digest(transition)
    return transition
