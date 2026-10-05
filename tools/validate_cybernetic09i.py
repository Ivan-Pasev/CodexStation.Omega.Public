#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from cybernetic09i.acquisition import make_request,aggregate

PREVIOUS="3d5282a9f1649c63555db3813bbbc6cc76035cd039e7ab8f5acff051af827a84"
FILES=[
 "cybernetic09i/ACQUISITION_PROTOCOL.json",
 "cybernetic09i/ACQUISITION_LEDGER.json",
 "cybernetic09i/REQUESTS.json",
 "cybernetic09i/acquisition.py",
 "tests/test_cybernetic09i.py",
 "tools/build_acquisition_packets09i.py",
 "tools/validate_cybernetic09i.py",
 "publication/SLICE_09I_RECEIPT.json"
]
def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()
def main():
    errors=[]
    ledger=json.loads((ROOT/"cybernetic09i/ACQUISITION_LEDGER.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09I_RECEIPT.json").read_text())
    if aggregate(ledger)["status"]!="HOLD_LIVE_RECEIPTS_PENDING": errors.append("live ledger must remain pending")
    reqs=[make_request(h) for h in ("chatgpt-codex","gemini-notebook")]
    if len({r["challenge_digest"] for r in reqs})!=2: errors.append("host challenges must differ")
    if receipt.get("live_receipts_ingested")!=0: errors.append("slice must not claim live receipt ingestion")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_LIVE_HOST_WITNESS_ACQUISITION_SLICE_09I",
      "ledger_status":aggregate(ledger)["status"],
      "requests":[{"host_id":r["host_id"],"request_id":r["request_id"],"challenge_digest":r["challenge_digest"]} for r in reqs],
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "live_receipts_ingested":0,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
