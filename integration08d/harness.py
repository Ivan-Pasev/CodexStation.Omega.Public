"""Source-bound Tier-A integration harness for CodexStation Ω v0.8d.

The harness intentionally executes only local source-derived fixtures against
the 08C adapters/runtime. It does not execute or vendor source repositories.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from runtime08c.adapters import (
    adapt_digital_fabrica_transition,
    adapt_dfpl_gateway_request,
    adapt_gilc_effect_intent,
    adapt_highestone_state,
    adapt_neural_lattice_state,
)
from runtime08c.runtime import (
    compile_archetonic_plate,
    digest,
    execute_transition,
    make_state,
    plan_digest,
    recovery_check,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "integration08d" / "SOURCE_FIXTURES.json"


def _load() -> list[dict[str, Any]]:
    return json.loads(FIXTURES.read_text())["fixtures"]


def _grant(principal: str, level: str = "A2", rights: list[str] | None = None) -> dict[str, Any]:
    return {
        "grant_id": f"grant:{principal}",
        "principal_id": principal,
        "level": level,
        "rights": list(rights or []),
        "scope": ["*"],
    }


def _inv() -> list[dict[str, Any]]:
    return [{"invariant_id": "inv:root", "status": "PASS", "evidence_refs": ["fixture:08d"]}]


def _result(fixture: dict[str, Any], *, status: str, observations: dict[str, Any], residuals: list[str] | None = None) -> dict[str, Any]:
    return {
        "fixture_id": fixture["fixture_id"],
        "source_family": fixture["source_family"],
        "repository": fixture["repository"],
        "commit": fixture["commit"],
        "status": status,
        "observations": observations,
        "residuals": list(residuals if residuals is not None else fixture.get("residuals", [])),
        "evidence_class": fixture["evidence_class"],
    }


def run_digital_fabrica(f: dict[str, Any]) -> dict[str, Any]:
    state = make_state(project_id="p08d", grants=[_grant("actor:dfc", "A2")])
    native = copy.deepcopy(f["native"])
    native["parentStateHash"] = state["digest"]
    proposal = {
        "transition_id": native["id"],
        "parent_state_digest": native["parentStateHash"],
        "actor_id": native["proposer"],
        "kind": native["kind"],
        "operations": native["operations"],
        "required_authority": [native["requiredAuthority"]],
        "protected_invariants": native["protectedInvariants"],
        "verification_plan": native["verificationPlan"],
        "reversibility": native["reversibility"],
        "evidence_refs": ["source:Digital.Fabrica.Core@c3e142d"],
    }
    transition = adapt_digital_fabrica_transition(proposal, project_id="p08d")
    transition["authorized_plan_digest"] = plan_digest(transition)
    out = execute_transition(state, transition, semantic_decision={"status": "ALLOW"}, invariant_results=_inv())

    stale = copy.deepcopy(transition)
    stale["transition_id"] = "dfc:stale"
    stale["parent_state_digest"] = digest("canonical-state", {"foreign": True})
    stale["authorized_plan_digest"] = plan_digest(stale)
    stale_out = execute_transition(state, stale, semantic_decision={"status": "ALLOW"}, invariant_results=_inv())

    ok = out["status"] == "PASS" and stale_out["status"] == "HOLD" and "STALE_OR_FOREIGN_PARENT" in stale_out["receipt"]["decision_vector"]["admission"]["reasons"]
    return _result(f, status="PASS_WITH_RESIDUALS" if ok else "FAIL", observations={
        "runtime_status": out["status"],
        "event": None if out["event"] is None else out["event"]["event_type"],
        "stale_parent_status": stale_out["status"],
        "normalization": f["normalization"]["transforms"],
    })


def run_dfpl(f: dict[str, Any]) -> dict[str, Any]:
    state = make_state(project_id="p08d", grants=[_grant("actor:dfpl", "A0", ["Tool.Invoke"])])
    request = copy.deepcopy(f["native"]["gateway_request"])
    request["parent_state_digest"] = state["digest"]
    auth = copy.deepcopy(f["native"]["authorization"])
    auth["plan_digest"] = digest("authorized-plan", request["operations"])
    transition = adapt_dfpl_gateway_request(request, auth, project_id="p08d")
    out = execute_transition(state, transition, semantic_decision={"status": "ALLOW"}, invariant_results=_inv())

    tampered = copy.deepcopy(transition)
    tampered["operations"] = tampered["operations"] + [{"op": "SET", "key": "tampered", "value": 1}]
    tampered_out = execute_transition(state, tampered, semantic_decision={"status": "ALLOW"}, invariant_results=_inv())
    ok = out["status"] == "PASS" and tampered_out["status"] == "HOLD" and "AUTHORIZED_PLAN_BINDING_MISMATCH" in tampered_out["receipt"]["decision_vector"]["admission"]["reasons"]
    return _result(f, status="PASS_WITH_RESIDUALS" if ok else "FAIL", observations={
        "runtime_status": out["status"],
        "tampered_plan_status": tampered_out["status"],
        "exact_plan_binding_enforced": ok,
    })


def run_highestone(f: dict[str, Any]) -> dict[str, Any]:
    source = copy.deepcopy(f["native"])
    state = adapt_highestone_state(source, project_id="p08d-highest")
    transition = compile_archetonic_plate(
        plate_id="highest:memory",
        project_id="p08d-highest",
        state=state,
        principal_id="42",
        operations=[{"op": "SET", "key": "memory", "value": "retained"}],
        required_authority=["A2"],
        protected_invariants=["inv:root"],
    )
    out = execute_transition(state, transition, semantic_decision={"status": "ALLOW"}, invariant_results=_inv())
    rec = recovery_check(state, out["state"], out["receipt"]) if out["status"] == "PASS" else {"status": "QUARANTINE"}

    unauth_state = make_state(project_id="p08d-highest", grants=[])
    escalation = compile_archetonic_plate(
        plate_id="highest:bootstrap",
        project_id="p08d-highest",
        state=unauth_state,
        principal_id="42",
        operations=[{"op":"GRANT","grant":_grant("42","A4")}],
        required_authority=["A2"],
        protected_invariants=["inv:root"],
        kind="OPERATIONAL",
    )
    blocked = execute_transition(unauth_state, escalation, semantic_decision={"status":"ALLOW"}, invariant_results=_inv())
    ok = state["revision"] == 3 and out["status"] == "PASS" and rec["status"] == "RECOVERABLE" and blocked["status"] == "HOLD"
    return _result(f, status="PASS_WITH_RESIDUALS" if ok else "FAIL", observations={
        "adapted_revision": state["revision"],
        "runtime_status": out["status"],
        "recovery": rec["status"],
        "successor_authority_bootstrap": blocked["status"],
    })


def run_gilc(f: dict[str, Any]) -> dict[str, Any]:
    native = f["native"]
    state = make_state(project_id="p08d-gilc", grants=[_grant(native["actor"], native["required_authority"])])
    normalized = {
        "intent_id": "gilc:effect:1",
        "principal_id": native["actor"],
        "effect_type": native["operation"],
        "parameters": {"target": native["target"], **native.get("metadata", {})},
        "required_authority": native["required_authority"],
        "protected_invariants": ["inv:root"],
        "reversibility": "UNKNOWN",
        "evidence_refs": ["source:GILC.CodexStation@dae8c25"],
    }
    transition = adapt_gilc_effect_intent(normalized, state, project_id="p08d-gilc")
    out = execute_transition(state, transition, semantic_decision={"status":"ALLOW"}, invariant_results=_inv())
    ok = out["status"] == "UNKNOWN_OUTCOME" and out["state"]["digest"] == state["digest"] and out["event"] is None
    return _result(f, status="PASS_WITH_RESIDUALS" if ok else "FAIL", observations={
        "runtime_status_without_executor": out["status"],
        "successor_created": out["state"]["digest"] != state["digest"],
        "normalization": f["normalization"]["transforms"],
    })


def run_neural_lattice(f: dict[str, Any]) -> dict[str, Any]:
    native = copy.deepcopy(f["native"])
    adapter_input = copy.deepcopy(native)
    adapter_input["provenance"] = list(native["provenance"]["sources"])
    state = adapt_neural_lattice_state(adapter_input, project_id="p08d-nl")
    conflicts = state.get("conflicts", [])
    ok = state["revision"] == 4 and len(conflicts) == 1 and conflicts[0]["status"] == "UNRESOLVED" and "source:nl" in state["provenance_refs"]
    return _result(f, status="PASS_WITH_RESIDUALS" if ok else "FAIL", observations={
        "adapted_revision": state["revision"],
        "conflict_durable": bool(conflicts),
        "conflict_status": conflicts[0]["status"] if conflicts else None,
        "provenance_refs": state["provenance_refs"],
        "normalization": f["normalization"]["transforms"],
    })


RUNNERS = {
    "DIGITAL_FABRICA_CORE": run_digital_fabrica,
    "DFPL_PRIMA": run_dfpl,
    "HIGHESTONE": run_highestone,
    "GILC_CODEXSTATION": run_gilc,
    "NEURAL_LATTICE": run_neural_lattice,
}


def run_all() -> dict[str, Any]:
    results = [RUNNERS[f["source_family"]](f) for f in _load()]
    return {
        "harness_id": "cs.harness::tier-a-integration::v0.8d",
        "result": "PASS" if all(x["status"].startswith("PASS") for x in results) else "FAIL",
        "source_families": len(results),
        "results": results,
        "authority_delta": "NONE",
        "release_eligible": False,
    }


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2))
