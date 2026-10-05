#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from cybernetic09n.dedup import audit

PREVIOUS="c964d45b46ea0466c1972c04f2b25fd036fa096cd83e7b81855e54eb8a176d7f"
FILES=[
 "cybernetic09n/DEDUP_SCOPE.json",
 "cybernetic09n/SUPERSESSION_REGISTRY.json",
 "cybernetic09n/dedup.py",
 "tests/test_cybernetic09n.py",
 "tools/validate_cybernetic09n.py",
 "publication/SLICE_09N_RECEIPT.json"
]
def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()
def main():
    errors=[]
    manifest=json.loads((ROOT/"MANIFEST.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09N_RECEIPT.json").read_text())
    result=audit()
    if result["status"]!="PASS": errors.extend(result["errors"])
    if manifest.get("publication_gates",{}).get("duplication_dedup")!="PASS":
        errors.append({"code":"MANIFEST_DEDUP_GATE_NOT_PASS"})
    if receipt.get("dedup_gate")!="PASS":
        errors.append({"code":"RECEIPT_DEDUP_GATE_NOT_PASS"})
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_PUBLICATION_OBJECT_IDENTITY_DEDUP_SUPERSESSION_SLICE_09N",
      "audit":result,
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
