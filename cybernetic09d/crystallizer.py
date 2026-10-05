"""Bounded adaptive policy and telemetry crystallization for CodexStation Omega v0.9d."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
POLICY=json.loads((ROOT/"cybernetic09d/ADAPTIVE_POLICY.json").read_text())

def canonical_bytes(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(value:Any)->str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def policy_digest(policy:dict[str,Any])->str:
    return digest({"domain":"adaptive-policy-09d","policy":policy})

def summarize(records:list[dict[str,Any]])->dict[str,dict[str,Any]]:
    by={}
    for r in records:
        skill=r.get("skill_uri")
        if not skill:
            continue
        x=by.setdefault(skill,{"sample_count":0,"PASS":0,"RECOVERED":0,"FALLBACK":0,"HOLD":0,"FAIL":0,"QUARANTINE":0,"UNKNOWN_OUTCOME":0})
        x["sample_count"]+=1
        status=r.get("step_status","HOLD")
        if status in x:
            x[status]+=1
    out={}
    min_samples=int(POLICY["minimum_samples_for_health"])
    for skill,x in by.items():
        n=x["sample_count"]
        success=(x["PASS"]+x["RECOVERED"])/n if n else 0.0
        failure=(x["FAIL"]+x["QUARANTINE"])/n if n else 0.0
        hold=(x["HOLD"]+x["UNKNOWN_OUTCOME"])/n if n else 0.0
        fallback=x["FALLBACK"]/n if n else 0.0
        if n<min_samples:
            health="UNKNOWN"
        elif success>=POLICY["thresholds"]["healthy_success_rate"]:
            health="HEALTHY"
        elif success>=POLICY["thresholds"]["watch_success_rate"]:
            health="WATCH"
        else:
            health="DEGRADED"
        out[skill]={
            **x,
            "success_rate":round(success,6),
            "failure_rate":round(failure,6),
            "hold_rate":round(hold,6),
            "fallback_rate":round(fallback,6),
            "health":health
        }
    return out

def score_skill(skill_uri:str, summary:dict[str,dict[str,Any]], policy:dict[str,Any]|None=None)->dict[str,Any]:
    p=policy or POLICY
    s=summary.get(skill_uri)
    if not s:
        return {"skill_uri":skill_uri,"score":p["scoring"]["base_score"],"health":"UNKNOWN","sample_count":0}
    sc=p["scoring"]
    score=sc["base_score"]
    score+=s["PASS"]*sc["pass_bonus"]
    score+=s["RECOVERED"]*sc["recovered_bonus"]
    score-=s["FALLBACK"]*sc["fallback_penalty"]
    score-=s["HOLD"]*sc["hold_penalty"]
    score-=s["FAIL"]*sc["fail_penalty"]
    score-=s["QUARANTINE"]*sc["quarantine_penalty"]
    return {"skill_uri":skill_uri,"score":score,"health":s["health"],"sample_count":s["sample_count"]}

def rank_admissible(candidates:list[dict[str,Any]], records:list[dict[str,Any]], policy:dict[str,Any]|None=None)->dict[str,Any]:
    p=copy.deepcopy(policy or POLICY)
    summary=summarize(records)
    admissible=[copy.deepcopy(x) for x in candidates if x.get("admissible") is True]
    ranked=[]
    for c in admissible:
        hint=score_skill(c["skill_uri"],summary,p)
        ranked.append({**c,"adaptive_hint":hint})
    ranked.sort(key=lambda x:(-x["adaptive_hint"]["score"],x["skill_uri"]))
    return {
        "policy_version":p["policy_version"],
        "policy_digest":policy_digest(p),
        "routing_order":[x["skill_uri"] for x in ranked],
        "candidates":ranked,
        "summary":summary,
        "authority_delta":"NONE"
    }

def crystallize_failure_patterns(records:list[dict[str,Any]])->list[dict[str,Any]]:
    buckets={}
    for r in records:
        key=(r.get("skill_uri"),r.get("failure_code"),r.get("recovery_action"))
        if key[0] is None or key[1] in (None,""):
            continue
        buckets[key]=buckets.get(key,0)+1
    out=[]
    for (skill,failure,recovery),count in sorted(buckets.items()):
        out.append({
            "pattern_id":digest({"skill":skill,"failure":failure,"recovery":recovery})[:16],
            "skill_uri":skill,
            "failure_code":failure,
            "recovery_action":recovery,
            "count":count,
            "advisory_only":True
        })
    return out

def propose_policy_update(records:list[dict[str,Any]], current_policy:dict[str,Any]|None=None)->dict[str,Any]:
    current=copy.deepcopy(current_policy or POLICY)
    summary=summarize(records)
    degraded=sorted(k for k,v in summary.items() if v["health"]=="DEGRADED")
    proposal=copy.deepcopy(current)
    proposal["policy_version"]=int(current["policy_version"])+1
    proposal["derived_from_policy_digest"]=policy_digest(current)
    proposal["advisory_skill_watchlist"]=degraded
    proposal["authority_delta"]="NONE"
    return {
        "status":"PROPOSAL_ONLY",
        "proposal":proposal,
        "proposal_digest":policy_digest(proposal),
        "does_not_change":["skill qualification","authority ceiling","evidence ceiling","truth status"],
        "authority_delta":"NONE"
    }

def replay(records:list[dict[str,Any]], candidates:list[dict[str,Any]], policy:dict[str,Any])->dict[str,Any]:
    first=rank_admissible(candidates,records,policy)
    second=rank_admissible(candidates,records,copy.deepcopy(policy))
    return {
        "deterministic":first["policy_digest"]==second["policy_digest"] and first["routing_order"]==second["routing_order"] and first["summary"]==second["summary"],
        "result":first
    }
