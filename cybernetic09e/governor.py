"""Adaptive-policy promotion/replay governor for CodexStation Omega v0.9e."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any
from cybernetic09d.crystallizer import policy_digest, replay

ROOT=Path(__file__).resolve().parents[1]
GOV=json.loads((ROOT/"cybernetic09e/PROMOTION_POLICY.json").read_text())

def canonical(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(value:Any)->str:
    return hashlib.sha256(canonical(value)).hexdigest()

def semantic_diff(current:dict[str,Any],proposal:dict[str,Any])->dict[str,Any]:
    changed=[]
    for key in sorted(set(current)|set(proposal)):
        if current.get(key)!=proposal.get(key):
            changed.append(key)
    protected=[]
    for key in GOV["immutable_semantic_fields"]:
        if current.get(key)!=proposal.get(key):
            protected.append(key)
    return {"changed_fields":changed,"protected_field_changes":protected}

def verify_authorization(auth:dict[str,Any], proposal_digest:str, predecessor_digest:str)->dict[str,Any]:
    reasons=[]
    if not auth:
        return {"status":"HOLD","reasons":["AUTHORIZATION_MISSING"]}
    if auth.get("authority_level")!=GOV["governance_authorization"]["required_level"]:
        reasons.append("AUTHORITY_LEVEL_MISMATCH")
    if GOV["governance_authorization"]["required_right"] not in auth.get("rights",[]):
        reasons.append("POLICY_PROMOTE_RIGHT_MISSING")
    if auth.get("proposal_digest")!=proposal_digest:
        reasons.append("PROPOSAL_DIGEST_MISMATCH")
    if auth.get("predecessor_policy_digest")!=predecessor_digest:
        reasons.append("PREDECESSOR_DIGEST_MISMATCH")
    if not auth.get("authorization_id") or not auth.get("principal_id"):
        reasons.append("AUTHORIZATION_IDENTITY_INCOMPLETE")
    return {"status":"PASS" if not reasons else "HOLD","reasons":reasons}

def verify_replay_witness(proposal:dict[str,Any], telemetry:list[dict[str,Any]], candidates:list[dict[str,Any]], witness:dict[str,Any])->dict[str,Any]:
    r=replay(telemetry,candidates,proposal)
    reasons=[]
    if not r["deterministic"]:
        reasons.append("NONDETERMINISTIC_REPLAY")
    result=r["result"]
    if witness.get("policy_digest")!=result["policy_digest"]:
        reasons.append("POLICY_DIGEST_MISMATCH")
    if witness.get("routing_order")!=result["routing_order"]:
        reasons.append("ROUTING_ORDER_MISMATCH")
    if witness.get("summary_digest")!=digest(result["summary"]):
        reasons.append("SUMMARY_DIGEST_MISMATCH")
    return {"status":"PASS" if not reasons else "HOLD","reasons":reasons,"computed":result}

def validate_proposal(current:dict[str,Any], proposal:dict[str,Any], telemetry:list[dict[str,Any]], candidates:list[dict[str,Any]], witness:dict[str,Any], authorization:dict[str,Any])->dict[str,Any]:
    reasons=[]
    predecessor=policy_digest(current)
    proposal_d=policy_digest(proposal)
    if proposal.get("derived_from_policy_digest")!=predecessor:
        reasons.append("PREDECESSOR_POLICY_IDENTITY_FAIL")
    if proposal.get("policy_version")!=int(current.get("policy_version",0))+1:
        reasons.append("POLICY_VERSION_NOT_INCREMENTAL")
    diff=semantic_diff(current,proposal)
    if diff["protected_field_changes"]:
        reasons.append("PROTECTED_POLICY_SEMANTICS_CHANGED")
    if proposal.get("authority_delta")!="NONE":
        reasons.append("AUTHORITY_DELTA_NONZERO")
    replay_check=verify_replay_witness(proposal,telemetry,candidates,witness)
    if replay_check["status"]!="PASS":
        reasons.extend(replay_check["reasons"])
    auth=verify_authorization(authorization,proposal_d,predecessor)
    if auth["status"]!="PASS":
        reasons.extend(auth["reasons"])
    return {
        "status":"PASS" if not reasons else "HOLD",
        "reasons":sorted(set(reasons)),
        "proposal_digest":proposal_d,
        "predecessor_policy_digest":predecessor,
        "diff":diff,
        "replay":replay_check,
        "authorization":auth
    }

def promote(registry:dict[str,Any], current:dict[str,Any], proposal:dict[str,Any], telemetry:list[dict[str,Any]], candidates:list[dict[str,Any]], witness:dict[str,Any], authorization:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    verdict=validate_proposal(current,proposal,telemetry,candidates,witness,authorization)
    if verdict["status"]!="PASS":
        return copy.deepcopy(registry),{"status":"HOLD",**verdict}
    out=copy.deepcopy(registry)
    previous=copy.deepcopy(out["active_policy"])
    new_active={
      "policy_id":proposal["policy_id"],
      "policy_version":proposal["policy_version"],
      "policy_digest":verdict["proposal_digest"],
      "source":"PROMOTED_PROPOSAL",
      "status":"ACTIVE"
    }
    receipt={
      "schema":"GILC/CODEXSTATION/OMEGA-POLICY-PROMOTION-RECEIPT/0.9e",
      "authorization_id":authorization["authorization_id"],
      "principal_id":authorization["principal_id"],
      "predecessor_policy_digest":verdict["predecessor_policy_digest"],
      "promoted_policy_digest":verdict["proposal_digest"],
      "policy_version":proposal["policy_version"],
      "replay_witness_digest":digest(witness),
      "authority_delta":"NONE"
    }
    out["predecessor"]=previous
    out["active_policy"]=new_active
    out["promotion_receipt"]=receipt
    out["rollback_pointer"]=previous
    return out,{"status":"PROMOTED","receipt":receipt,"verdict":verdict}

def rollback_policy(registry:dict[str,Any], *, authorization:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    if not registry.get("rollback_pointer"):
        return copy.deepcopy(registry),{"status":"HOLD","reason":"NO_ROLLBACK_POINTER"}
    if authorization.get("authority_level")!=GOV["governance_authorization"]["required_level"] or "POLICY_PROMOTE" not in authorization.get("rights",[]):
        return copy.deepcopy(registry),{"status":"HOLD","reason":"ROLLBACK_AUTHORIZATION_MISSING"}
    out=copy.deepcopy(registry)
    current=copy.deepcopy(out["active_policy"])
    target=copy.deepcopy(out["rollback_pointer"])
    out["active_policy"]=target
    out["predecessor"]=current
    out["rollback_pointer"]=None
    out["promotion_receipt"]={
      "schema":"GILC/CODEXSTATION/OMEGA-POLICY-ROLLBACK-RECEIPT/0.9e",
      "authorization_id":authorization.get("authorization_id"),
      "from_policy_digest":current["policy_digest"],
      "to_policy_digest":target["policy_digest"],
      "scope":"ROUTING_POLICY_ONLY",
      "authority_delta":"NONE"
    }
    return out,{"status":"ROLLED_BACK","scope":"ROUTING_POLICY_ONLY"}
