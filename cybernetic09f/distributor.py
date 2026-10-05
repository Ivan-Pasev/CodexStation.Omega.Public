"""Multi-host policy distribution and deterministic replay parity for Omega v0.9f."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any
from cybernetic09d.crystallizer import replay, policy_digest

ROOT=Path(__file__).resolve().parents[1]
HOSTS_DOC=json.loads((ROOT/"cybernetic09f/HOST_PROFILES.json").read_text())
HOSTS={x["host_id"]:x for x in HOSTS_DOC["hosts"]}

def canonical(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(value:Any)->str:
    return hashlib.sha256(canonical(value)).hexdigest()

def active_policy(registry:dict[str,Any], policy_object:dict[str,Any])->dict[str,Any]:
    active=registry["active_policy"]
    computed=policy_digest(policy_object)
    return {
      "policy_id":active["policy_id"],
      "policy_version":active["policy_version"],
      "registry_digest":active["policy_digest"],
      "computed_digest":computed,
      "status":"PASS" if active["policy_digest"]==computed else "HOLD"
    }

def host_profile_digest(host_id:str)->str:
    if host_id not in HOSTS:
        raise KeyError(host_id)
    return digest(HOSTS[host_id])

def distribute(host_id:str, registry:dict[str,Any], policy_object:dict[str,Any], telemetry:list[dict[str,Any]], candidates:list[dict[str,Any]])->dict[str,Any]:
    if host_id not in HOSTS:
        return {"host_id":host_id,"status":"HOLD_PROFILE_INVALID","reasons":["UNKNOWN_HOST"]}
    ap=active_policy(registry,policy_object)
    if ap["status"]!="PASS":
        return {"host_id":host_id,"status":"HOLD_POLICY_MISMATCH","reasons":["ACTIVE_POLICY_REGISTRY_DIGEST_MISMATCH"]}
    rr=replay(telemetry,candidates,policy_object)
    result=rr["result"]
    status="PARITY_PASS"
    reasons=[]
    if not rr["deterministic"]:
        status="HOLD_REPLAY_DIVERGENCE"; reasons.append("NONDETERMINISTIC_REPLAY")
    if result["policy_digest"]!=ap["registry_digest"]:
        status="HOLD_POLICY_MISMATCH"; reasons.append("REPLAY_POLICY_DIGEST_MISMATCH")
    return {
      "schema":"GILC/CODEXSTATION/OMEGA-HOST-POLICY-RECEIPT/0.9f",
      "host_id":host_id,
      "active_policy_digest":ap["registry_digest"],
      "policy_version":ap["policy_version"],
      "replay_policy_digest":result["policy_digest"],
      "routing_order":result["routing_order"],
      "summary_digest":digest(result["summary"]),
      "host_profile_digest":host_profile_digest(host_id),
      "host_capability_profile":copy.deepcopy(HOSTS[host_id]["capability_profile"]),
      "status":status,
      "reasons":reasons,
      "authority_delta":"NONE"
    }

def compare_receipts(receipts:list[dict[str,Any]])->dict[str,Any]:
    if not receipts:
        return {"status":"HOLD","reasons":["NO_RECEIPTS"]}
    reasons=[]
    policy_digests={r.get("active_policy_digest") for r in receipts}
    replay_digests={r.get("replay_policy_digest") for r in receipts}
    routing={tuple(r.get("routing_order",[])) for r in receipts}
    summaries={r.get("summary_digest") for r in receipts}
    if len(policy_digests)!=1: reasons.append("ACTIVE_POLICY_DIGEST_DIVERGENCE")
    if len(replay_digests)!=1: reasons.append("REPLAY_POLICY_DIGEST_DIVERGENCE")
    if len(routing)!=1: reasons.append("ROUTING_ORDER_DIVERGENCE")
    if len(summaries)!=1: reasons.append("SUMMARY_DIVERGENCE")
    if any(r.get("status")!="PARITY_PASS" for r in receipts): reasons.append("HOST_RECEIPT_NOT_PASS")
    return {
      "status":"PARITY_PASS" if not reasons else "HOLD_DIVERGENCE",
      "reasons":reasons,
      "hosts":[r.get("host_id") for r in receipts],
      "policy_digest":next(iter(policy_digests)) if len(policy_digests)==1 else None,
      "authority_delta":"NONE"
    }

def tamper_receipt(receipt:dict[str,Any], *, routing_order:list[str]|None=None, replay_policy_digest:str|None=None)->dict[str,Any]:
    out=copy.deepcopy(receipt)
    if routing_order is not None:
        out["routing_order"]=routing_order
    if replay_policy_digest is not None:
        out["replay_policy_digest"]=replay_policy_digest
    return out
