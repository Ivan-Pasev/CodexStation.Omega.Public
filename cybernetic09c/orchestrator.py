"""Recoverable skill-binding orchestration fabric for CodexStation Omega v0.9c."""
from __future__ import annotations
import copy, json
from pathlib import Path
from typing import Any, Callable
from cybernetic09b.compiler import compile_plan, execute_plan, critique, recovery_decision

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=json.loads((ROOT/"cybernetic09c/SKILL_REGISTRY.json").read_text())
SKILLS={x["skill_uri"]:x for x in REGISTRY["skills"]}

def skill_matches(skill:dict[str,Any], step:dict[str,Any])->bool:
    intent=(step.get("intent") or "").lower()
    tags=skill.get("intent_tags",[])
    return any(tag.lower() in intent for tag in tags) or step.get("skill_uri")==skill.get("skill_uri")

def bind_skill(step:dict[str,Any], capability_state:dict[str,str], grants:list[str])->dict[str,Any]:
    candidates=[]
    for skill in SKILLS.values():
        if not skill_matches(skill,step):
            continue
        reasons=[]
        if skill.get("status")!="QUALIFIED_PUBLIC_SEED":
            reasons.append("SKILL_NOT_QUALIFIED")
        missing_caps=[c for c in skill.get("required_capabilities",[]) if capability_state.get(c)!="OBSERVED"]
        if missing_caps:
            reasons.append("SKILL_CAPABILITY_MISSING")
        required_auth=step.get("required_authority",[])
        ceiling=skill.get("authority_ceiling","A0")
        try:
            ceiling_n=int(ceiling[1:])
        except Exception:
            ceiling_n=-1
        for req in required_auth:
            if req.startswith("A"):
                try:
                    if int(req[1:])>ceiling_n:
                        reasons.append("SKILL_AUTHORITY_CEILING_EXCEEDED")
                except Exception:
                    reasons.append("INVALID_AUTHORITY_LEVEL")
            if req not in grants:
                reasons.append("MISSION_AUTHORITY_MISSING")
        candidates.append({"skill_uri":skill["skill_uri"],"status":"PASS" if not reasons else "HOLD","reasons":sorted(set(reasons)),"skill":skill})
    passed=[x for x in candidates if x["status"]=="PASS"]
    if passed:
        return passed[0]
    if candidates:
        return candidates[0]
    return {"skill_uri":None,"status":"HOLD","reasons":["NO_MATCHING_SKILL"],"skill":None}

def topological_steps(steps:list[dict[str,Any]])->list[dict[str,Any]]:
    by={x["step_id"]:copy.deepcopy(x) for x in steps}
    out=[]
    resolved=set()
    while len(out)<len(by):
        ready=[x for x in by.values() if x["step_id"] not in resolved and set(x.get("depends_on",[])).issubset(resolved)]
        if not ready:
            raise ValueError("dependency graph contains cycle or missing dependency")
        ready=sorted(ready,key=lambda x:x["step_id"])
        for step in ready:
            out.append(step); resolved.add(step["step_id"])
    return out

def evidence_rank(value:str)->int:
    ranks={"NONE":0,"FORMALIZATION_ONLY":1,"IMPLEMENTATION":2,"PUBLICATION_ADMISSIBILITY":2}
    return ranks.get(value,0)

def fallback_allowed(primary:dict[str,Any], fallback:dict[str,Any])->bool:
    pa=int(primary.get("authority_ceiling","A0")[1:])
    fa=int(fallback.get("authority_ceiling","A0")[1:])
    return fa<=pa and evidence_rank(fallback.get("evidence_ceiling","NONE"))<=evidence_rank(primary.get("evidence_ceiling","NONE"))

def step_to_mission(step:dict[str,Any])->dict[str,Any]:
    return {
      "id":"mission:"+step["step_id"],
      "intent":step.get("intent",""),
      "mode":step.get("mode","LOCAL_VERIFICATION"),
      "required_capabilities":list(step.get("required_capabilities",[])),
      "required_authority":list(step.get("required_authority",[]))
    }

def orchestrate(*,project_id:str,principal_id:str,steps:list[dict[str,Any]],state:dict[str,Any],capability_state:dict[str,str],grants:list[str],invariant_results:dict[str,list[dict[str,Any]]]|None=None,effect_receipts:dict[str,list[dict[str,Any]]]|None=None,executor:Callable[[dict[str,Any],dict[str,Any]],dict[str,Any]]|None=None)->dict[str,Any]:
    ordered=topological_steps(steps)
    status_by={}
    receipts=[]
    telemetry=[]
    current=state
    invariant_results=invariant_results or {}
    effect_receipts=effect_receipts or {}

    for step in ordered:
        deps=step.get("depends_on",[])
        if any(status_by.get(d) not in {"PASS","RECOVERED"} for d in deps):
            status_by[step["step_id"]]="HOLD"
            receipts.append({"step_id":step["step_id"],"status":"HOLD","reason":"DEPENDENCY_NOT_CLOSED"})
            continue

        binding=bind_skill(step,capability_state,grants)
        if binding["status"]!="PASS":
            status_by[step["step_id"]]="HOLD"
            receipts.append({"step_id":step["step_id"],"status":"HOLD","reason":"SKILL_BINDING_FAILED","binding":binding})
            telemetry.append({"step_id":step["step_id"],"skill_uri":binding.get("skill_uri"),"attempts":0,"status":"HOLD","failure_code":"SKILL_BINDING_FAILED","recovery_action":"NONE"})
            continue

        skill=binding["skill"]
        mission=step_to_mission(step)
        plan=compile_plan(
          mission,project_id=project_id,principal_id=principal_id,
          local_operations=step.get("local_operations",[]),
          external_effects=step.get("external_effects",[]),
          protected_invariants=step.get("protected_invariants",[]),
          reversibility=step.get("reversibility","UNKNOWN")
        )

        max_attempts=max(1,int(step.get("max_attempts",1)))
        attempts=0
        result=None
        while attempts<max_attempts:
            attempts+=1
            if executor is None:
                result=execute_plan(
                  plan,state=current,capability_state=capability_state,grants=grants,
                  invariant_results=invariant_results.get(step["step_id"],[]),
                  effect_receipts=effect_receipts.get(step["step_id"],[])
                )
            else:
                result=executor(plan,current)
            if result.get("status")=="PASS":
                break
            if result.get("status")=="UNKNOWN_OUTCOME":
                break
            if attempts>=max_attempts:
                break

        crit=critique(plan,result)
        recovery=recovery_decision(plan,result,current)

        final=result.get("status","HOLD")
        action="NONE"
        if final=="PASS":
            current=result.get("state",current)
        elif final=="FAIL" and recovery["status"]=="RECOVER_PREDECESSOR":
            final="RECOVERED"; action="RECOVER_PREDECESSOR"
        elif final in {"FAIL","UNKNOWN_OUTCOME"} and recovery["status"]=="QUARANTINE":
            final="QUARANTINE"; action="QUARANTINE"

        fallback_uri=step.get("fallback_skill_uri")
        if final in {"HOLD","FAIL"} and fallback_uri:
            fb=SKILLS.get(fallback_uri)
            if fb and fallback_allowed(skill,fb):
                final="FALLBACK"; action="FALLBACK:"+fallback_uri

        status_by[step["step_id"]]=final
        receipts.append({
          "step_id":step["step_id"],"skill_uri":skill["skill_uri"],
          "status":final,"attempts":attempts,"plan_digest":plan["plan_digest"],
          "execution_status":result.get("status"),"critique":crit,"recovery":recovery,
          "evidence_ceiling":skill.get("evidence_ceiling"),"authority_ceiling":skill.get("authority_ceiling")
        })
        telemetry.append({
          "step_id":step["step_id"],"skill_uri":skill["skill_uri"],"attempts":attempts,
          "status":final,"failure_code":None if final=="PASS" else result.get("reason",result.get("phase",final)),
          "recovery_action":action
        })

    mission_status="PASS"
    if any(v=="QUARANTINE" for v in status_by.values()):
        mission_status="QUARANTINE"
    elif any(v in {"HOLD","FAIL","UNKNOWN_OUTCOME"} for v in status_by.values()):
        mission_status="HOLD"
    elif any(v=="FALLBACK" for v in status_by.values()):
        mission_status="PARTIAL"
    return {
      "status":mission_status,
      "state":current,
      "step_status":status_by,
      "receipts":receipts,
      "telemetry":telemetry,
      "authority_delta":"NONE"
    }
