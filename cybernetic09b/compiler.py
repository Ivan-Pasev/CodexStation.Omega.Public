"""Typed mission compiler and effect gate for CodexStation Omega v0.9b."""
from __future__ import annotations
import copy
from typing import Any
from runtime08c.runtime import digest, execute_transition, make_state, plan_digest

def canonical_plan_material(plan:dict[str,Any])->dict[str,Any]:
    return {
        "mission_id":plan["mission_id"],
        "project_id":plan["project_id"],
        "principal_id":plan["principal_id"],
        "mode":plan["mode"],
        "intent":plan["intent"],
        "required_capabilities":list(plan.get("required_capabilities",[])),
        "required_authority":list(plan.get("required_authority",[])),
        "local_operations":copy.deepcopy(plan.get("local_operations",[])),
        "external_effects":copy.deepcopy(plan.get("external_effects",[])),
        "protected_invariants":list(plan.get("protected_invariants",[])),
        "reversibility":plan.get("reversibility","UNKNOWN"),
    }

def compile_plan(mission:dict[str,Any], *, project_id:str, principal_id:str, local_operations:list[dict[str,Any]]|None=None, external_effects:list[dict[str,Any]]|None=None, protected_invariants:list[str]|None=None, reversibility:str="UNKNOWN")->dict[str,Any]:
    plan={
        "plan_id":"plan:"+mission["id"],
        "mission_id":mission["id"],
        "project_id":project_id,
        "principal_id":principal_id,
        "mode":mission.get("mode","LOCAL_VERIFICATION"),
        "intent":mission.get("intent",""),
        "required_capabilities":list(mission.get("required_capabilities",[])),
        "required_authority":list(mission.get("required_authority",[])),
        "local_operations":copy.deepcopy(local_operations or []),
        "external_effects":copy.deepcopy(external_effects or []),
        "protected_invariants":list(protected_invariants or []),
        "reversibility":reversibility,
        "authority_delta":"NONE",
    }
    for i,effect in enumerate(plan["external_effects"]):
        effect.setdefault("effect_id",f"{plan['mission_id']}:effect:{i+1}")
    plan["plan_digest"]=digest("mission-plan",canonical_plan_material(plan))
    return plan

def verify_plan_digest(plan:dict[str,Any])->bool:
    return plan.get("plan_digest")==digest("mission-plan",canonical_plan_material(plan))

def capability_bind(plan:dict[str,Any], capability_state:dict[str,str])->dict[str,Any]:
    missing=[c for c in plan.get("required_capabilities",[]) if capability_state.get(c)!="OBSERVED"]
    return {"status":"PASS" if not missing else "HOLD","missing":missing}

def authority_bind(plan:dict[str,Any], grants:list[str])->dict[str,Any]:
    missing=[a for a in plan.get("required_authority",[]) if a not in grants]
    return {"status":"PASS" if not missing else "HOLD","missing":missing}

def local_transition(plan:dict[str,Any], state:dict[str,Any])->dict[str,Any]:
    transition={
        "transition_id":plan["plan_id"]+":local",
        "project_id":plan["project_id"],
        "parent_state_digest":state["digest"],
        "proposer_principal_id":plan["principal_id"],
        "kind":"OPERATIONAL",
        "operations":copy.deepcopy(plan["local_operations"]),
        "required_authority":list(plan["required_authority"]),
        "protected_invariants":list(plan["protected_invariants"]),
        "verification_plan":[],
        "reversibility":plan["reversibility"],
        "evidence_refs":["plan:"+plan["plan_digest"]["value"]],
        "source_profile":"OMEGA_09B",
    }
    transition["authorized_plan_digest"]=plan_digest(transition)
    return transition

def prepare_effect_envelopes(plan:dict[str,Any])->list[dict[str,Any]]:
    return [{
        "effect_id":e["effect_id"],
        "plan_digest":plan["plan_digest"],
        "effect":copy.deepcopy(e),
        "status":"PENDING",
        "authority_delta":"NONE",
    } for e in plan["external_effects"]]

def verify_effect_receipt(envelope:dict[str,Any], receipt:dict[str,Any])->dict[str,Any]:
    reasons=[]
    if receipt.get("effect_id")!=envelope["effect_id"]:
        reasons.append("EFFECT_ID_MISMATCH")
    if receipt.get("plan_digest")!=envelope["plan_digest"]:
        reasons.append("PLAN_DIGEST_MISMATCH")
    if receipt.get("status") not in {"PASS","FAIL","UNKNOWN_OUTCOME"}:
        reasons.append("INVALID_EFFECT_STATUS")
    if not receipt.get("observer"):
        reasons.append("OBSERVER_MISSING")
    if receipt.get("status") in {"PASS","FAIL"} and not receipt.get("evidence_refs"):
        reasons.append("EVIDENCE_MISSING")
    return {
        "status":"PASS" if not reasons else "REJECT",
        "reasons":reasons,
        "effect_outcome":receipt.get("status") if not reasons else "UNKNOWN_OUTCOME",
    }

def execute_plan(plan:dict[str,Any], *, state:dict[str,Any], capability_state:dict[str,str], grants:list[str], invariant_results:list[dict[str,Any]], effect_receipts:list[dict[str,Any]]|None=None)->dict[str,Any]:
    if not verify_plan_digest(plan):
        return {"status":"HOLD","reason":"PLAN_DIGEST_INVALID","state":state}
    cap=capability_bind(plan,capability_state)
    auth=authority_bind(plan,grants)
    if cap["status"]!="PASS":
        return {"status":"HOLD","reason":"CAPABILITY_BINDING_FAILED","capability":cap,"state":state}
    if auth["status"]!="PASS":
        return {"status":"HOLD","reason":"AUTHORITY_BINDING_FAILED","authority":auth,"state":state}

    current=state
    local_result=None
    if plan["local_operations"]:
        transition=local_transition(plan,current)
        local_result=execute_transition(
            current,transition,
            semantic_decision={"status":"ALLOW"},
            invariant_results=invariant_results,
        )
        if local_result["status"]!="PASS":
            return {"status":local_result["status"],"phase":"LOCAL","local":local_result,"state":current}
        current=local_result["state"]

    envelopes=prepare_effect_envelopes(plan)
    receipt_by_id={r.get("effect_id"):r for r in (effect_receipts or [])}
    effect_results=[]
    for envelope in envelopes:
        receipt=receipt_by_id.get(envelope["effect_id"])
        if receipt is None:
            effect_results.append({"effect_id":envelope["effect_id"],"status":"UNKNOWN_OUTCOME","verification":"NO_RECEIPT"})
            continue
        verdict=verify_effect_receipt(envelope,receipt)
        effect_results.append({
            "effect_id":envelope["effect_id"],
            "status":verdict["effect_outcome"],
            "verification":verdict["status"],
            "reasons":verdict["reasons"],
        })

    if any(x["verification"]=="REJECT" for x in effect_results):
        return {"status":"HOLD","phase":"EFFECT_VERIFY","effects":effect_results,"local":local_result,"state":current}
    if any(x["status"]=="FAIL" for x in effect_results):
        return {"status":"FAIL","phase":"EFFECT","effects":effect_results,"local":local_result,"state":current}
    if any(x["status"]=="UNKNOWN_OUTCOME" for x in effect_results):
        return {"status":"UNKNOWN_OUTCOME","phase":"EFFECT","effects":effect_results,"local":local_result,"state":current}
    return {"status":"PASS","phase":"CLOSED","effects":effect_results,"local":local_result,"state":current}

def critique(plan:dict[str,Any], result:dict[str,Any])->dict[str,Any]:
    issues=[]
    if result.get("status")=="UNKNOWN_OUTCOME":
        issues.append("EXTERNAL_EFFECT_NOT_CLOSED")
    if result.get("status")=="FAIL":
        issues.append("EXECUTION_FAILURE")
    if result.get("status")=="HOLD":
        issues.append("ADMISSION_OR_VERIFICATION_HOLD")
    if plan.get("reversibility")=="IRREVERSIBLE" and plan.get("external_effects"):
        issues.append("IRREVERSIBLE_EXTERNAL_EFFECT")
    return {"status":"PASS" if not issues else "ATTENTION","issues":issues}

def recovery_decision(plan:dict[str,Any], result:dict[str,Any], predecessor_state:dict[str,Any])->dict[str,Any]:
    if result.get("status")=="PASS":
        return {"status":"NOT_REQUIRED","target_state":result["state"]}
    if plan.get("reversibility")!="REVERSIBLE":
        return {"status":"QUARANTINE","reason":"PLAN_NOT_DECLARED_REVERSIBLE","target_state":result.get("state",predecessor_state)}
    if result.get("phase")=="LOCAL" and result.get("status")=="FAIL":
        return {"status":"RECOVER_PREDECESSOR","target_state":predecessor_state}
    if result.get("phase")=="EFFECT":
        return {"status":"QUARANTINE","reason":"EXTERNAL_EFFECT_STATE_NOT_ROLLBACK_PROVEN","target_state":result.get("state",predecessor_state)}
    return {"status":"RECOVER_PREDECESSOR","target_state":predecessor_state}
