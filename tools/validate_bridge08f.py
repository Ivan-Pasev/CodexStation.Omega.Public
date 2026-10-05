#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from tools.verify_private_receipt08f import synthetic_example, verify

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS="3c140cbdb00ca9e5725ce0742928d8a9085f2649c7bddffb4b18e6f352c0b5c7"
FILES=[
 "bridge08f/EXPECTED_PINS.json",
 "bridge08f/RECEIPT_SCHEMA.json",
 "bridge08f/RUN_PROTOCOL.md",
 "tools/verify_private_receipt08f.py",
 "publication/SLICE_08F_RECEIPT.json",
 "tools/validate_bridge08f.py",
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes()
        h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest()
    return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    pins=json.loads((ROOT/"bridge08f/EXPECTED_PINS.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_08F_RECEIPT.json").read_text())
    families={x["source_family"] for x in pins.get("sources",[])}
    if families!={"DIGITAL_FABRICA_CORE","HIGHESTONE","NEURAL_LATTICE"}:
        errors.append("private-family pin set mismatch")
    if pins.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    if receipt.get("release_eligible") is not False:
        errors.append("release eligibility must remain false")
    if receipt.get("status")!="BRIDGE_IMPLEMENTED_EXECUTION_HOLD":
        errors.append("bridge status mismatch")
    if receipt.get("previous_composite_semantic_fingerprint")!=PREVIOUS:
        errors.append("predecessor fingerprint mismatch")
    if verify(synthetic_example()):
        errors.append("receipt ABI self-check failed")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_TIER_A_PRIVATE_REPRODUCTION_BRIDGE_SLICE_08F",
      "bridge_status":receipt.get("status"),
      "held_execution_families":sorted(families),
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
