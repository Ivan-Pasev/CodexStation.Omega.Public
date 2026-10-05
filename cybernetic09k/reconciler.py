"""Evidence-frontier reconciler and anti-spin scheduler for Omega v0.9k."""
from __future__ import annotations
import copy, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
GRAPH=json.loads((ROOT/"cybernetic09k/EVIDENCE_FRONTIER_GRAPH.json").read_text())
POLICY=json.loads((ROOT/"cybernetic09k/FRONTIER_SCHEDULER_POLICY.json").read_text())
GATES={g["gate_id"]:g for g in GRAPH["gates"]}

def classify_gate(gate:dict[str,Any], evidence_delta:bool=False, governance_delta:bool=False)->dict[str,Any]:
    cls=gate["classification"]
    if evidence_delta and cls in {"EXTERNAL_EVIDENCE_PENDING","EXTERNAL_OR_ENVIRONMENTAL_EVIDENCE_PENDING"}:
        decision="RESUME"
    elif governance_delta and cls=="GOVERNANCE_DECISION_PENDING":
        decision="RESUME"
    elif cls=="IMPLEMENTATION_GAP":
        decision="IMPLEMENT_NOW"
    elif cls in {"EXTERNAL_EVIDENCE_PENDING","EXTERNAL_OR_ENVIRONMENTAL_EVIDENCE_PENDING"}:
        decision="WAIT_FOR_EVIDENCE"
    elif cls=="GOVERNANCE_DECISION_PENDING":
        decision="REQUEST_GOVERNANCE"
    else:
        decision="HOLD_RELEASE"
    return {
        "gate_id":gate["gate_id"],
        "classification":cls,
        "architecture_state":gate["architecture_state"],
        "current_state":gate["current_state"],
        "decision":decision,
        "resume_condition":gate["resume_condition"],
        "minimal_admissible_evidence":copy.deepcopy(gate["minimal_admissible_evidence"])
    }

def schedule(evidence_deltas:dict[str,bool]|None=None, governance_deltas:dict[str,bool]|None=None)->dict[str,Any]:
    evidence_deltas=evidence_deltas or {}
    governance_deltas=governance_deltas or {}
    decisions=[
        classify_gate(g,evidence_deltas.get(g["gate_id"],False),governance_deltas.get(g["gate_id"],False))
        for g in GRAPH["gates"]
    ]
    resumable=[d["gate_id"] for d in decisions if d["decision"]=="RESUME"]
    implementation=[d["gate_id"] for d in decisions if d["decision"]=="IMPLEMENT_NOW"]
    governance=[d["gate_id"] for d in decisions if d["decision"]=="REQUEST_GOVERNANCE"]
    waiting=[d["gate_id"] for d in decisions if d["decision"]=="WAIT_FOR_EVIDENCE"]
    next_action=("RESUME:"+resumable[0] if resumable else
                 "IMPLEMENT:"+implementation[0] if implementation else
                 "GOVERNANCE:"+governance[0] if governance else
                 "WAIT_FOR_EVIDENCE")
    return {
        "decisions":decisions,
        "resumable":resumable,
        "implementation_now":implementation,
        "governance_pending":governance,
        "waiting_for_evidence":waiting,
        "next_action":next_action,
        "authority_delta":"NONE"
    }

def evidence_requirements(gate_id:str)->dict[str,Any]:
    if gate_id not in GATES:
        return {"status":"UNKNOWN_GATE","gate_id":gate_id}
    g=GATES[gate_id]
    return {
        "status":"KNOWN",
        "gate_id":gate_id,
        "minimal_admissible_evidence":copy.deepcopy(g["minimal_admissible_evidence"]),
        "admission_surface":g["admission_surface"],
        "resume_condition":g["resume_condition"],
        "dependencies":copy.deepcopy(g["dependencies"])
    }

def stable_without_delta()->bool:
    return schedule()==schedule()
