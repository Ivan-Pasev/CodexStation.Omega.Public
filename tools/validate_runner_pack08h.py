#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS="f557bd38c1cfa705ea37a1d97168b7ff218e85e9abdd8086e5aa23cd97795488"
FILES=[
 "runner08h/FAMILY_PROFILES.json",
 "runner08h/run_source.py",
 "runner08h/README.md",
 "tools/validate_runner_pack08h.py",
 "tools/build_runner_pack08h.py",
 "tests/test_runner08h.py",
 "publication/SLICE_08H_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    profiles=json.loads((ROOT/"runner08h/FAMILY_PROFILES.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_08H_RECEIPT.json").read_text())
    families=profiles.get("families",{})
    if set(families)!={"DIGITAL_FABRICA_CORE","HIGHESTONE","NEURAL_LATTICE"}:
        errors.append("family profile mismatch")
    for family,p in families.items():
        if len(p.get("source_commit",""))!=40:
            errors.append("invalid pin:"+family)
        if not p.get("steps"):
            errors.append("missing steps:"+family)
        if not p.get("scope"):
            errors.append("missing scope:"+family)
    if profiles.get("output_contract")!="GILC/CODEXSTATION/OMEGA-PRIVATE-REPRODUCTION-RECEIPT/0.8f":
        errors.append("output contract mismatch")
    if profiles.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    if receipt.get("status")!="RUNNER_PACK_IMPLEMENTED_EXECUTION_PENDING":
        errors.append("slice status mismatch")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_TIER_A_RESTRICTED_RUNNER_EXECUTION_PACK_SLICE_08H",
      "families":sorted(families),
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
