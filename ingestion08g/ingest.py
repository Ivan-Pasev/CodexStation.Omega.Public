"""Fail-closed 08G receipt ingestion engine."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
PINS_DOC=json.loads((ROOT/"bridge08f/EXPECTED_PINS.json").read_text())
PINS={x["source_family"]:x for x in PINS_DOC["sources"]}

def canonical_digest(receipt:dict[str,Any])->str:
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def _base_verify(receipt:dict[str,Any])->list[str]:
    errors=[]
    if receipt.get("schema")!="GILC/CODEXSTATION/OMEGA-PRIVATE-REPRODUCTION-RECEIPT/0.8f":
        errors.append("SCHEMA_MISMATCH")
    family=receipt.get("source_family")
    pin=PINS.get(family)
    if pin is None:
        return errors+["UNKNOWN_SOURCE_FAMILY"]
    if receipt.get("repository")!=pin["repository"]:
        errors.append("REPOSITORY_MISMATCH")
    if receipt.get("source_commit")!=pin["source_commit"]:
        errors.append("SOURCE_COMMIT_MISMATCH")
    if receipt.get("sanitized") is not True:
        errors.append("NOT_SANITIZED")
    if receipt.get("private_source_disclosed") is not False:
        errors.append("SOURCE_DISCLOSURE_FORBIDDEN")
    if receipt.get("source_tree_modified_for_test") is not False:
        errors.append("SOURCE_MUTATION_FORBIDDEN")
    if receipt.get("authority_delta")!="NONE":
        errors.append("AUTHORITY_DELTA_FORBIDDEN")
    runner=receipt.get("runner_identity")
    if not isinstance(runner,dict) or not runner.get("provider") or runner.get("run_id") in (None,"") or not runner.get("runner_commit"):
        errors.append("RUNNER_IDENTITY_INCOMPLETE")
    if receipt.get("scope")!=pin["expected_receipt_scope"]:
        errors.append("SCOPE_MISMATCH")
    commands=receipt.get("commands")
    if not isinstance(commands,list):
        errors.append("COMMAND_VECTOR_MISSING")
        commands=[]
    results=receipt.get("results")
    if not isinstance(results,list):
        errors.append("RESULT_VECTOR_MISSING")
        results=[]
    by_result={x.get("command"):x.get("status") for x in results if isinstance(x,dict)}
    for cmd in pin["native_commands"]:
        if cmd not in commands:
            errors.append("REQUIRED_COMMAND_MISSING:"+cmd)
        if by_result.get(cmd) not in ("PASS","FAIL","SKIP"):
            errors.append("REQUIRED_RESULT_MISSING:"+cmd)
    if receipt.get("overall_status") not in ("PASS","FAIL","HOLD"):
        errors.append("OVERALL_STATUS_INVALID")
    return errors

def classify(receipt:dict[str,Any])->dict[str,Any]:
    family=receipt.get("source_family")
    digest=canonical_digest(receipt)
    errors=_base_verify(receipt)
    evidence_class=str(receipt.get("evidence_class",""))
    if any(marker in evidence_class.upper() for marker in ("SYNTHETIC","SCHEMA_TEST","SOURCE_REPORTED")):
        return {"family":family,"verdict":"REJECT_NON_EXECUTION_EVIDENCE","receipt_digest":digest,"errors":errors or ["NON_EXECUTION_EVIDENCE_CLASS"]}
    if errors:
        return {"family":family,"verdict":"REJECT_INVALID_RECEIPT","receipt_digest":digest,"errors":errors}
    pin=PINS[family]
    results={x["command"]:x["status"] for x in receipt["results"]}
    required=[results[x] for x in pin["native_commands"]]
    overall=receipt["overall_status"]
    if overall=="FAIL" or "FAIL" in required:
        verdict="FAIL_REPRODUCTION"
    elif overall=="HOLD" or "SKIP" in required:
        verdict="HOLD_INCOMPLETE"
    elif overall=="PASS" and all(x=="PASS" for x in required):
        verdict="PASS_REPRODUCED"
    else:
        verdict="REJECT_INVALID_RECEIPT"
    return {"family":family,"verdict":verdict,"receipt_digest":digest,"evidence_scope":receipt.get("scope"),"errors":[]}

def ingest(registry:dict[str,Any],receipt:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    out=copy.deepcopy(registry)
    decision=classify(receipt)
    family=decision.get("family")
    if family not in PINS:
        return out,decision
    prior=out["families"][family]
    if prior.get("receipt_digest") and prior["receipt_digest"]!=decision["receipt_digest"]:
        conflict={**decision,"prior_receipt_digest":prior["receipt_digest"],"verdict":"REJECT_CONFLICT"}
        out["conflicts"].append(conflict)
        return out,conflict
    if decision["verdict"].startswith("REJECT_"):
        return out,decision
    out["families"][family]={
        "source_commit":PINS[family]["source_commit"],
        "verdict":decision["verdict"],
        "receipt_digest":decision["receipt_digest"],
        "evidence_scope":decision.get("evidence_scope")
    }
    if decision["receipt_digest"] not in [x["receipt_digest"] for x in out["admitted_receipts"]]:
        out["admitted_receipts"].append({
            "source_family":family,
            "source_commit":PINS[family]["source_commit"],
            "receipt_digest":decision["receipt_digest"],
            "verdict":decision["verdict"],
            "evidence_scope":decision.get("evidence_scope")
        })
    return out,decision
