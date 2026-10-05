"""Challenge-bound live host witness acquisition for CodexStation Omega v0.9i."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
HOSTS_DOC=json.loads((ROOT/"cybernetic09f/HOST_PROFILES.json").read_text())
HOSTS={x["host_id"]:x for x in HOSTS_DOC["hosts"]}
ACTIVE=json.loads((ROOT/"cybernetic09e/ACTIVE_POLICY_REGISTRY.json").read_text())["active_policy"]
from cybernetic09f.distributor import host_profile_digest
from cybernetic09g.conformance import classify_witness

def canonical(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(v:Any)->str:
    return hashlib.sha256(canonical(v)).hexdigest()

def make_request(host_id:str)->dict[str,Any]:
    if host_id not in HOSTS:
        raise KeyError(host_id)
    request_id=f"acq09i-{host_id}-v1"
    material={
      "request_id":request_id,
      "host_id":host_id,
      "host_profile_digest":host_profile_digest(host_id),
      "active_policy_digest":ACTIVE["policy_digest"],
      "policy_version":ACTIVE["policy_version"],
      "runner_pack":{
        "artifact_name":"codexstation-omega-host-witness-v0.9h",
        "artifact_id":11346428555,
        "inner_zip_sha256":"4e6de4f89facf18e39a9dbec3c75372539ce5f0202b1ab4d72e09270f895a1ec"
      },
      "expires_after_use":True
    }
    challenge_id="challenge:"+digest(material)[:24]
    challenge_digest=digest({"domain":"omega-09i-challenge","challenge_id":challenge_id,"material":material})
    return {**material,"challenge_id":challenge_id,"challenge_digest":challenge_digest}

def verify_return(request:dict[str,Any], returned:dict[str,Any], ledger:dict[str,Any])->dict[str,Any]:
    reasons=[]
    host=request["host_id"]
    if returned.get("request_id")!=request["request_id"]:
        reasons.append("REQUEST_ID_MISMATCH")
    if returned.get("challenge_id")!=request["challenge_id"]:
        reasons.append("CHALLENGE_ID_MISMATCH")
    if returned.get("challenge_digest")!=request["challenge_digest"]:
        reasons.append("CHALLENGE_DIGEST_MISMATCH")
    entry=ledger.get("hosts",{}).get(host)
    if not entry:
        reasons.append("HOST_NOT_IN_LEDGER")
    elif entry.get("challenge_consumed"):
        reasons.append("CHALLENGE_ALREADY_CONSUMED")
    witness=returned.get("host_witness")
    if not isinstance(witness,dict):
        reasons.append("HOST_WITNESS_MISSING")
        witness_verdict={"status":"REJECT_INVALID_WITNESS","reasons":["HOST_WITNESS_MISSING"]}
    else:
        if witness.get("host_id")!=host:
            reasons.append("RETURN_HOST_MISMATCH")
        witness_verdict=classify_witness(witness)
        if witness_verdict["status"]!="LIVE_CONFORMANCE_PASS":
            reasons.append("09G_NOT_LIVE_CONFORMANCE_PASS")
    return {
      "status":"PASS" if not reasons else "HOLD",
      "reasons":sorted(set(reasons)),
      "host_id":host,
      "witness_verdict":witness_verdict,
      "returned_digest":digest(returned)
    }

def ingest_return(ledger:dict[str,Any], request:dict[str,Any], returned:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    out=copy.deepcopy(ledger)
    verdict=verify_return(request,returned,out)
    host=request["host_id"]
    if verdict["status"]!="PASS":
        return out,verdict
    entry=out["hosts"][host]
    entry["acquisition_state"]="LIVE_CONFORMANCE_PASS"
    entry["admitted_witness_digest"]=verdict["witness_verdict"]["witness_digest"]
    entry["challenge_consumed"]=True
    out["live_multi_host_conformance_closed"]=all(
      x["acquisition_state"]=="LIVE_CONFORMANCE_PASS" for x in out["hosts"].values()
    )
    return out,{"status":"INGESTED","host_id":host,"live_multi_host_conformance_closed":out["live_multi_host_conformance_closed"]}

def aggregate(ledger:dict[str,Any])->dict[str,Any]:
    states={k:v["acquisition_state"] for k,v in ledger["hosts"].items()}
    if all(v=="LIVE_CONFORMANCE_PASS" for v in states.values()):
        status="LIVE_MULTI_HOST_CONFORMANCE_PASS"
    elif any(v=="LIVE_CONFORMANCE_FAIL" for v in states.values()):
        status="FAIL_LIVE_MULTI_HOST_CONFORMANCE"
    else:
        status="HOLD_LIVE_RECEIPTS_PENDING"
    return {"status":status,"host_states":states,"authority_delta":"NONE"}
