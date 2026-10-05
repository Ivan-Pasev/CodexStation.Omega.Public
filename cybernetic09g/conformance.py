"""Live host witness ingestion and conformance gate for CodexStation Omega v0.9g."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
HOSTS_DOC=json.loads((ROOT/"cybernetic09f/HOST_PROFILES.json").read_text())
HOSTS={x["host_id"]:x for x in HOSTS_DOC["hosts"]}
ACTIVE=json.loads((ROOT/"cybernetic09e/ACTIVE_POLICY_REGISTRY.json").read_text())
EXPECTED_POLICY=ACTIVE["active_policy"]["policy_digest"]

def canonical(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(value:Any)->str:
    return hashlib.sha256(canonical(value)).hexdigest()

def expected_profile_digest(host_id:str)->str|None:
    host=HOSTS.get(host_id)
    return digest(host) if host else None

def classify_witness(witness:dict[str,Any])->dict[str,Any]:
    reasons=[]
    host_id=witness.get("host_id")
    expected_profile=expected_profile_digest(host_id)
    origin=witness.get("witness_origin")
    if host_id not in HOSTS:
        reasons.append("UNKNOWN_HOST")
    if expected_profile is not None and witness.get("host_profile_digest")!=expected_profile:
        reasons.append("HOST_PROFILE_DIGEST_MISMATCH")
    if witness.get("active_policy_digest")!=EXPECTED_POLICY:
        reasons.append("ACTIVE_POLICY_DIGEST_MISMATCH")
    if witness.get("replay_policy_digest")!=EXPECTED_POLICY:
        reasons.append("REPLAY_POLICY_DIGEST_MISMATCH")
    if witness.get("policy_version")!=ACTIVE["active_policy"]["policy_version"]:
        reasons.append("POLICY_VERSION_MISMATCH")
    env=witness.get("environment")
    if not isinstance(env,dict):
        reasons.append("ENVIRONMENT_MISSING")
    else:
        for key in ("runtime","runtime_version","adapter_version","capability_observations"):
            if key not in env:
                reasons.append("ENVIRONMENT_FIELD_MISSING:"+key)
    if origin not in {"LIVE_HOST","SYNTHETIC_TEST","REFERENCE_IMPLEMENTATION"}:
        reasons.append("WITNESS_ORIGIN_INVALID")
    if witness.get("status") not in {"PASS","FAIL","UNKNOWN_OUTCOME"}:
        reasons.append("WITNESS_STATUS_INVALID")
    if witness.get("status")=="PASS" and not witness.get("execution_id"):
        reasons.append("EXECUTION_ID_MISSING")
    if reasons:
        return {"status":"REJECT_INVALID_WITNESS","reasons":reasons,"witness_digest":digest(witness),"host_id":host_id}
    if origin!="LIVE_HOST":
        return {"status":"HOLD_NON_LIVE_WITNESS","reasons":["NON_LIVE_ORIGIN"],"witness_digest":digest(witness),"host_id":host_id}
    if witness["status"]=="FAIL":
        return {"status":"FAIL_HOST_CONFORMANCE","reasons":[],"witness_digest":digest(witness),"host_id":host_id}
    if witness["status"]=="UNKNOWN_OUTCOME":
        return {"status":"HOLD_HOST_UNKNOWN_OUTCOME","reasons":[],"witness_digest":digest(witness),"host_id":host_id}
    return {"status":"LIVE_CONFORMANCE_PASS","reasons":[],"witness_digest":digest(witness),"host_id":host_id}

def ingest(registry:dict[str,Any], witness:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    out=copy.deepcopy(registry)
    verdict=classify_witness(witness)
    host_id=verdict.get("host_id")
    if verdict["status"].startswith("REJECT_") or host_id not in out.get("hosts",{}):
        out["rejected_witnesses"].append({
          "host_id":host_id,
          "witness_digest":verdict["witness_digest"],
          "status":verdict["status"],
          "reasons":verdict["reasons"]
        })
        return out,verdict
    if verdict["status"]=="HOLD_NON_LIVE_WITNESS":
        return out,verdict
    out["hosts"][host_id]["state"]=verdict["status"]
    out["hosts"][host_id]["witness_digest"]=verdict["witness_digest"]
    if verdict["witness_digest"] not in [x["witness_digest"] for x in out["admitted_live_witnesses"]]:
        out["admitted_live_witnesses"].append({
          "host_id":host_id,
          "witness_digest":verdict["witness_digest"],
          "status":verdict["status"],
          "execution_id":witness.get("execution_id")
        })
    return out,verdict

def aggregate(registry:dict[str,Any])->dict[str,Any]:
    states={k:v["state"] for k,v in registry["hosts"].items()}
    if all(v=="LIVE_CONFORMANCE_PASS" for v in states.values()):
        status="LIVE_MULTI_HOST_CONFORMANCE_PASS"
    elif any(v=="FAIL_HOST_CONFORMANCE" for v in states.values()):
        status="FAIL_LIVE_HOST_CONFORMANCE"
    elif any(v=="HOLD_HOST_UNKNOWN_OUTCOME" for v in states.values()):
        status="HOLD_LIVE_HOST_UNKNOWN_OUTCOME"
    else:
        status="HOLD_NO_COMPLETE_LIVE_HOST_WITNESSES"
    return {"status":status,"host_states":states,"authority_delta":"NONE"}
