#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = "d024fa3295770ac0db04cb7c7ed946bf42e6cf17130f9eee059dee3cf7770df7"
FILES = [
    ".github/workflows/reproduce-tier-a-08e.yml",
    "reproduction08e/REPRODUCTION_PROFILE.json",
    "reproduction08e/REPRODUCTION_LEDGER.json",
    "aggregation08e/REPRODUCTION_CONTRACT.md",
    "tests/test_reproduction08e.py",
    "tools/validate_reproduction08e.py",
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes()
        h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest()
    return s, hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    p=json.loads((ROOT/"reproduction08e/REPRODUCTION_PROFILE.json").read_text())
    l=json.loads((ROOT/"reproduction08e/REPRODUCTION_LEDGER.json").read_text())
    if p.get("previous_composite_semantic_fingerprint") != PREVIOUS:
        errors.append("predecessor fingerprint mismatch")
    if p.get("authority_delta")!="NONE" or l.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    if p.get("release_eligible") is not False or l.get("release_eligible") is not False:
        errors.append("release eligibility must remain false")
    if len(l.get("sources",[])) != 5:
        errors.append("expected five source families")
    by={x["source_family"]:x for x in l.get("sources",[])}
    for family in ("DIGITAL_FABRICA_CORE","HIGHESTONE","NEURAL_LATTICE"):
        if by.get(family,{}).get("independent_reproduction")!="HOLD":
            errors.append(f"private family promoted: {family}")
    if by.get("DFPL_PRIMA",{}).get("status")!="PARTIAL_SOURCE_NATIVE_REPRODUCTION_PENDING":
        errors.append("DFPL must remain partial until CI witness is bound")
    if by.get("GILC_CODEXSTATION",{}).get("status")!="INDEPENDENT_REPRODUCTION_PENDING":
        errors.append("GILC must remain pending until cross-repo CI witness is bound")
    if by.get("HIGHESTONE",{}).get("lineage_check",{}).get("relevant_formal_tree_changed") is not False:
        errors.append("HighestOne formal lineage not preserved")
    required={
        "SOURCE_REPORTED_PASS != LOCALLY_REPRODUCED_PASS",
        "SOURCE_NATIVE_RUN != INDEPENDENT_CROSS_REPO_REPRODUCTION",
        "UNCHANGED_RELEVANT_TREE != NEW_EXECUTION",
        "PARTIAL_NATIVE_TEST != FULL_SEMANTIC_CORRESPONDENCE",
        "HOLD != FAIL",
    }
    if not required.issubset(set(p.get("invariants",[]))):
        errors.append("required evidence invariants missing")
    sf,cf=fingerprint()
    report={
        "result":"PASS" if not errors else "FAIL",
        "reproduction_id":p["reproduction_id"],
        "source_families":5,
        "independent_targets":["DFPL_PRIMA:PARTIAL","GILC_CODEXSTATION:FULL_NATIVE_TEST_SUITE"],
        "private_holds":["DIGITAL_FABRICA_CORE","HIGHESTONE","NEURAL_LATTICE"],
        "slice_fingerprint":sf,
        "composite_semantic_fingerprint":cf,
        "authority_delta":"NONE",
        "release_eligible":False,
        "errors":errors,
    }
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
