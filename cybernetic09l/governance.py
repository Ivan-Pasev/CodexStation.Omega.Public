"""Governance decision and release-readiness evaluator for Omega v0.9l."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
GRAPH=json.loads((ROOT/"cybernetic09k/EVIDENCE_FRONTIER_GRAPH.json").read_text())
READINESS=json.loads((ROOT/"cybernetic09l/RELEASE_READINESS_POLICY.json").read_text())

def canonical(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(v:Any)->str:
    return hashlib.sha256(canonical(v)).hexdigest()

def decision_digest(decision:dict[str,Any])->str:
    d=copy.deepcopy(decision)
    d["authorization"]=None
    return digest({"domain":"omega-09l-governance-decision","decision":d})

def authorize_decision(decision:dict[str,Any], authorization:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    expected=decision_digest(decision)
    reasons=[]
    if not authorization:
        reasons.append("AUTHORIZATION_MISSING")
    else:
        if authorization.get("authority_level")!="A3":
            reasons.append("AUTHORITY_LEVEL_MISMATCH")
        if "GOVERNANCE_DECIDE" not in authorization.get("rights",[]):
            reasons.append("GOVERNANCE_DECIDE_RIGHT_MISSING")
        if authorization.get("decision_digest")!=expected:
            reasons.append("DECISION_DIGEST_MISMATCH")
        if not authorization.get("authorization_id") or not authorization.get("principal_id"):
            reasons.append("AUTHORIZATION_IDENTITY_INCOMPLETE")
    out=copy.deepcopy(decision)
    if reasons:
        return out,{"status":"HOLD","reasons":reasons,"decision_digest":expected}
    out["state"]="AUTHORIZED"
    out["authorization"]=copy.deepcopy(authorization)
    return out,{"status":"AUTHORIZED","reasons":[],"decision_digest":expected}

def publication_gate_state(manifest:dict[str,Any], authorized_license_decision:dict[str,Any]|None=None)->dict[str,str]:
    gates=copy.deepcopy(manifest.get("publication_gates",{}))
    if authorized_license_decision and authorized_license_decision.get("state")=="AUTHORIZED":
        gates["license_ip_review"]="GOVERNANCE_AUTHORIZED_DECISION_RECORDED"
    return gates

def unresolved_frontiers()->list[str]:
    unresolved=[]
    for g in GRAPH["gates"]:
        if g["gate_id"]=="LICENSE_IP_REVIEW":
            continue
        if g["current_state"] not in {"PASS","CLOSED","SATISFIED","COMPLETE"}:
            unresolved.append(g["gate_id"])
    return unresolved

def compute_release_readiness(manifest:dict[str,Any], authorized_license_decision:dict[str,Any]|None=None)->dict[str,Any]:
    gates=publication_gate_state(manifest,authorized_license_decision)
    gate_blockers=[]
    for g in READINESS["required_publication_gates"]:
        state=gates.get(g)
        if state not in {"PASS","PASS_CANDIDATE_BOOTSTRAP","GOVERNANCE_AUTHORIZED_DECISION_RECORDED"}:
            gate_blockers.append({"gate":g,"state":state})
    external=unresolved_frontiers()
    eligible=(not gate_blockers) and (not external)
    return {
      "release_eligible":eligible,
      "publication_gate_blockers":gate_blockers,
      "external_frontier_blockers":external,
      "license_decision_state":(authorized_license_decision or {}).get("state","PROPOSED"),
      "status":"RELEASE_CANDIDATE" if eligible else "RELEASE_HOLD",
      "authority_delta":"NONE"
    }
