#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from cybernetic09l.governance import compute_release_readiness

PREVIOUS="15be646c46117179f3d8372db17e2822c4c6224fb9ca89b297ca59cbb03cf8fb"
FILES=[
 "cybernetic09l/GOVERNANCE_DECISION_SCHEMA.json",
 "cybernetic09l/LICENSE_IP_DECISION.json",
 "cybernetic09l/RELEASE_READINESS_POLICY.json",
 "cybernetic09l/governance.py",
 "tests/test_cybernetic09l.py",
 "tools/validate_cybernetic09l.py",
 "publication/SLICE_09L_RECEIPT.json"
]
def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()
def main():
    errors=[]
    manifest=json.loads((ROOT/"MANIFEST.json").read_text())
    decision=json.loads((ROOT/"cybernetic09l/LICENSE_IP_DECISION.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09L_RECEIPT.json").read_text())
    readiness=compute_release_readiness(manifest,None)
    if decision.get("state")!="PROPOSED": errors.append("license decision must remain proposed without explicit authorization")
    if readiness["release_eligible"]: errors.append("release must remain ineligible")
    if receipt.get("license_ip_review_closed") is not False: errors.append("slice must not claim license/IP gate closure")
    if receipt.get("release_eligible") is not False: errors.append("slice must not claim release eligibility")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_GOVERNANCE_DECISION_AND_RELEASE_READINESS_SLICE_09L",
      "license_decision_state":decision["state"],
      "release_readiness":readiness,
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
