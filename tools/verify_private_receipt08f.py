#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PINS=json.loads((ROOT/"bridge08f/EXPECTED_PINS.json").read_text())
BY_FAMILY={x["source_family"]:x for x in PINS["sources"]}

def verify(receipt):
    errors=[]
    if receipt.get("schema")!="GILC/CODEXSTATION/OMEGA-PRIVATE-REPRODUCTION-RECEIPT/0.8f":
        errors.append("schema mismatch")
    family=receipt.get("source_family")
    pin=BY_FAMILY.get(family)
    if pin is None:
        return errors+["unknown source family"]
    if receipt.get("repository")!=pin["repository"]:
        errors.append("repository mismatch")
    if receipt.get("source_commit")!=pin["source_commit"]:
        errors.append("source commit mismatch")
    if receipt.get("sanitized") is not True:
        errors.append("receipt not sanitized")
    if receipt.get("private_source_disclosed") is not False:
        errors.append("source disclosure forbidden")
    if receipt.get("source_tree_modified_for_test") is not False:
        errors.append("source tree modification forbidden")
    if receipt.get("authority_delta")!="NONE":
        errors.append("authority promotion forbidden")
    commands=receipt.get("commands",[])
    results={x.get("command"):x.get("status") for x in receipt.get("results",[])}
    for cmd in pin["native_commands"]:
        if cmd not in commands:
            errors.append("required command missing: "+cmd)
        if results.get(cmd) not in ("PASS","FAIL","SKIP"):
            errors.append("missing result for: "+cmd)
    if receipt.get("overall_status")=="PASS":
        for cmd in pin["native_commands"]:
            if results.get(cmd)!="PASS":
                errors.append("PASS receipt contains non-PASS required command")
    return errors

def main():
    path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/"bridge08f/SAMPLE_RECEIPT.json"
    receipt=json.loads(path.read_text())
    errors=verify(receipt)
    print(json.dumps({"result":"PASS" if not errors else "FAIL","source_family":receipt.get("source_family"),"errors":errors},indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
