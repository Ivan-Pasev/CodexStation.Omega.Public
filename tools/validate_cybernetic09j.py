#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from cybernetic09j.ingestion import ingest_inbox

PREVIOUS="9bd7fef32e64225e378674c36ebf60487c04f6a683caeb438ceec66a90b07358"
FILES=[
 "cybernetic09j/RETURN_INGESTION_POLICY.json",
 "cybernetic09j/RETURN_INBOX.json",
 "cybernetic09j/ingestion.py",
 "tests/test_cybernetic09j.py",
 "tools/validate_cybernetic09j.py",
 "publication/SLICE_09J_RECEIPT.json"
]
def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()
def main():
    errors=[]
    ledger=json.loads((ROOT/"cybernetic09i/ACQUISITION_LEDGER.json").read_text())
    inbox=json.loads((ROOT/"cybernetic09j/RETURN_INBOX.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09J_RECEIPT.json").read_text())
    result=ingest_inbox(ledger,inbox)
    if result["status"]!="HOLD_NO_RETURNED_HOST_ENVELOPES": errors.append("empty inbox must hold")
    if result["counts"]["accepted"]!=0: errors.append("live receipt count must remain zero")
    if receipt.get("live_receipts_ingested")!=0: errors.append("slice receipt overclaims live ingestion")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_HOST_RETURN_INGESTION_AND_LIVE_CONFORMANCE_SLICE_09J",
      "ingestion_status":result["status"],
      "aggregate":result["aggregate"],
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "live_receipts_ingested":0,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
