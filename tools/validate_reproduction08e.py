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
    h = hashlib.sha256()
    for rel in FILES:
        raw = (ROOT / rel).read_bytes()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(raw)
        h.update(b"\0")
    slice_fp = h.hexdigest()
    composite = hashlib.sha256((PREVIOUS + "|" + slice_fp).encode()).hexdigest()
    return slice_fp, composite

def main():
    errors = []
    profile = json.loads((ROOT / "reproduction08e/REPRODUCTION_PROFILE.json").read_text())
    ledger = json.loads((ROOT / "reproduction08e/REPRODUCTION_LEDGER.json").read_text())

    if profile.get("previous_composite_semantic_fingerprint") != PREVIOUS:
        errors.append("predecessor fingerprint mismatch")
    if profile.get("authority_delta") != "NONE" or ledger.get("authority_delta") != "NONE":
        errors.append("authority delta must remain NONE")
    if profile.get("release_eligible") is not False or ledger.get("release_eligible") is not False:
        errors.append("release eligibility must remain false")

    sources = ledger.get("sources", [])
    if len(sources) != 5:
        errors.append("expected five source families")
    by = {x["source_family"]: x for x in sources}

    for family in ("DIGITAL_FABRICA_CORE", "HIGHESTONE", "NEURAL_LATTICE"):
        if by.get(family, {}).get("independent_reproduction") != "HOLD":
            errors.append(f"private family promoted: {family}")

    if by.get("DFPL_PRIMA", {}).get("status") != "PARTIAL_SOURCE_NATIVE_REPRODUCTION_PASS":
        errors.append("DFPL partial reproduction witness missing")
    if by.get("GILC_CODEXSTATION", {}).get("status") != "INDEPENDENT_CROSS_REPO_NATIVE_EXECUTION_PASS":
        errors.append("GILC independent reproduction witness missing")
    if by.get("DFPL_PRIMA", {}).get("independent_reproduction", {}).get("workflow_run_id") != 37280622913:
        errors.append("DFPL reproduction run mismatch")
    if by.get("GILC_CODEXSTATION", {}).get("independent_reproduction", {}).get("workflow_run_id") != 37280622913:
        errors.append("GILC reproduction run mismatch")
    if by.get("HIGHESTONE", {}).get("lineage_check", {}).get("relevant_formal_tree_changed") is not False:
        errors.append("HighestOne formal lineage not preserved")

    required = {
        "SOURCE_REPORTED_PASS != LOCALLY_REPRODUCED_PASS",
        "SOURCE_NATIVE_RUN != INDEPENDENT_CROSS_REPO_REPRODUCTION",
        "UNCHANGED_RELEVANT_TREE != NEW_EXECUTION",
        "PARTIAL_NATIVE_TEST != FULL_SEMANTIC_CORRESPONDENCE",
        "HOLD != FAIL",
    }
    if not required.issubset(set(profile.get("invariants", []))):
        errors.append("required evidence invariants missing")

    if ledger.get("aggregate_status") != "BOUNDED_REPRODUCTION_PASS_WITH_HOLDS":
        errors.append("aggregate reproduction status mismatch")

    slice_fp, composite = fingerprint()
    report = {
        "result": "PASS" if not errors else "FAIL",
        "reproduction_id": profile["reproduction_id"],
        "source_families": 5,
        "independent_results": {
            "DFPL_PRIMA": "PARTIAL_SOURCE_NATIVE_REPRODUCTION_PASS",
            "GILC_CODEXSTATION": "INDEPENDENT_CROSS_REPO_NATIVE_EXECUTION_PASS",
        },
        "private_holds": ["DIGITAL_FABRICA_CORE", "HIGHESTONE", "NEURAL_LATTICE"],
        "slice_fingerprint": slice_fp,
        "composite_semantic_fingerprint": composite,
        "authority_delta": "NONE",
        "release_eligible": False,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
