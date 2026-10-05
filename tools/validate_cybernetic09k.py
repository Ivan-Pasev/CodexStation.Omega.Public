#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from cybernetic09k.reconciler import schedule

PREVIOUS="0be842a754cdcbdeccb08bda090f719cb5c3d03d1e50b1100a323625abe4f2da"
FILES=[
 "cybernetic09k/EVIDENCE_FRONTIER_GRAPH.json",
 "cybernetic09k/FRONTIER_SCHEDULER_POLICY.json",
 "cybernetic09k/reconciler.py",
 "tests/test_cybernetic09k.py",
 "tools/validate_cybernetic09k.py",
 "publication/SLICE_09K_RECEIPT.json"
]
def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()
def main():
    errors=[]
    graph=json.loads((ROOT/"cybernetic09k/EVIDENCE_FRONTIER_GRAPH.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09K_RECEIPT.json").read_text())
    s=schedule()
    if s["implementation_now"]:
        errors.append("unexpected implementation gap remains")
    for gid in ("08I_RESTRICTED_EXECUTION_RECEIPTS","09J_LIVE_HOST_RETURNS"):
        if gid not in s["waiting_for_evidence"]:
            errors.append(gid+" should wait for evidence")
    if "LICENSE_IP_REVIEW" not in s["governance_pending"]:
        errors.append("license/IP governance gate missing")
    if receipt.get("authority_delta")!="NONE" or graph.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_EVIDENCE_FRONTIER_RECONCILIATION_SLICE_09K",
      "next_action":s["next_action"],
      "waiting_for_evidence":s["waiting_for_evidence"],
      "governance_pending":s["governance_pending"],
      "implementation_now":s["implementation_now"],
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
