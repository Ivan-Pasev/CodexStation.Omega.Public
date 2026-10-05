"""CodexStation Ω cybernetic control plane v0.9a.

Deterministic reference controller. It does not create authority or perform
external effects by itself.
"""
from __future__ import annotations
import copy, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
CAPS_DOC=json.loads((ROOT/"cybernetic09a/CAPABILITY_LATTICE.json").read_text())
POLICY=json.loads((ROOT/"cybernetic09a/CONTROL_POLICY.json").read_text())
FRONTIER_SEED=json.loads((ROOT/"cybernetic09a/FRONTIER_SEED.json").read_text())
CAPS={x["id"]:x for x in CAPS_DOC["capabilities"]}

def observe(*, capability_overrides:dict[str,str]|None=None, receipts:list[dict[str,Any]]|None=None)->dict[str,Any]:
    caps={k:v["status"] for k,v in CAPS.items()}
    for k,v in (capability_overrides or {}).items():
        if k in caps:
            caps[k]=v
    return {"capabilities":caps,"receipts":copy.deepcopy(receipts or [])}

def estimate(observation:dict[str,Any])->dict[str,Any]:
    return {
        "available":sorted(k for k,v in observation["capabilities"].items() if v=="OBSERVED"),
        "held":sorted(k for k,v in observation["capabilities"].items() if v in {"HELD_EXTERNAL","UNOBSERVED"}),
        "receipt_count":len(observation.get("receipts",[])),
    }

def capability_check(mission:dict[str,Any], observation:dict[str,Any])->dict[str,Any]:
    missing=[c for c in mission.get("required_capabilities",[]) if observation["capabilities"].get(c)!="OBSERVED"]
    return {"status":"PASS" if not missing else "HOLD","missing":missing}

def authority_check(mission:dict[str,Any], grants:list[str])->dict[str,Any]:
    missing=[a for a in mission.get("required_authority",[]) if a not in grants]
    return {"status":"PASS" if not missing else "HOLD","missing":missing}

def frontier(observation:dict[str,Any], grants:list[str], missions:list[dict[str,Any]]|None=None)->list[dict[str,Any]]:
    out=[]
    for mission in copy.deepcopy(missions or FRONTIER_SEED["missions"]):
        cap=capability_check(mission,observation)
        auth=authority_check(mission,grants)
        if cap["status"]!="PASS":
            status="HELD_CAPABILITY"
        elif auth["status"]!="PASS":
            status="HELD_AUTHORITY"
        else:
            status="ADMISSIBLE"
        mission["control"]={"capability":cap,"authority":auth}
        mission["status"]=status
        out.append(mission)
    return sorted(out,key=lambda x:(-x.get("priority",0),x["id"]))

def select(frontier_state:list[dict[str,Any]])->dict[str,Any]:
    for mission in frontier_state:
        if mission["status"]=="ADMISSIBLE":
            return {"status":"SELECTED","mission":mission}
    return {"status":"HOLD","mission":None}

def compile_mission(mission:dict[str,Any])->dict[str,Any]:
    return {
        "mission_id":mission["id"],
        "mode":mission["mode"],
        "intent":mission["intent"],
        "required_capabilities":mission["required_capabilities"],
        "required_authority":mission["required_authority"],
        "authority_delta":"NONE",
    }

def execute_local(compiled:dict[str,Any], executor=None)->dict[str,Any]:
    if compiled["mode"]=="LOCAL_VERIFICATION":
        result={"status":"PASS","effects":[],"receipt_type":"CYBERNETIC_LOCAL"}
    elif executor is None:
        result={"status":"UNKNOWN_OUTCOME","effects":[],"receipt_type":"CYBERNETIC_EXTERNAL"}
    else:
        result=executor(copy.deepcopy(compiled))
        if result.get("status") not in {"PASS","FAIL","UNKNOWN_OUTCOME"}:
            result["status"]="UNKNOWN_OUTCOME"
    return result

def verify(compiled:dict[str,Any], execution:dict[str,Any])->dict[str,Any]:
    if execution["status"]=="PASS" and compiled["mode"]=="LOCAL_VERIFICATION":
        return {"status":"VERIFIED","evidence_ceiling":"IMPLEMENTATION"}
    if execution["status"]=="FAIL":
        return {"status":"FAILED","evidence_ceiling":"IMPLEMENTATION"}
    return {"status":"UNKNOWN_OUTCOME","evidence_ceiling":"NONE"}

def learn(model:dict[str,Any], mission:dict[str,Any], verification:dict[str,Any])->dict[str,Any]:
    out=copy.deepcopy(model)
    stats=out.setdefault("mission_stats",{}).setdefault(mission["id"],{"verified":0,"failed":0,"unknown":0})
    if verification["status"]=="VERIFIED":
        stats["verified"]+=1
    elif verification["status"]=="FAILED":
        stats["failed"]+=1
    else:
        stats["unknown"]+=1
    out["authority_delta"]="NONE"
    return out

def cycle(*,grants:list[str],capability_overrides:dict[str,str]|None=None,missions:list[dict[str,Any]]|None=None,model:dict[str,Any]|None=None,executor=None)->dict[str,Any]:
    obs=observe(capability_overrides=capability_overrides)
    est=estimate(obs)
    fr=frontier(obs,grants,missions)
    sel=select(fr)
    if sel["status"]!="SELECTED":
        return {"status":"HOLD","observation":obs,"estimate":est,"frontier":fr,"selection":sel,"model":copy.deepcopy(model or {})}
    mission=sel["mission"]
    compiled=compile_mission(mission)
    execution=execute_local(compiled,executor=executor)
    verification=verify(compiled,execution)
    learned=learn(model or {},mission,verification)
    return {
        "status":verification["status"],
        "observation":obs,
        "estimate":est,
        "frontier":fr,
        "selection":sel,
        "compiled":compiled,
        "execution":execution,
        "verification":verification,
        "model":learned,
    }
