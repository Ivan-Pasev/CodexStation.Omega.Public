#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from cybernetic09h.run_host_witness import build_witness
from cybernetic09g.conformance import classify_witness

PREVIOUS="f0c807fff1abb2df627cbc40467b45a59feb0a53201147a4fb685d03baad93d7"
FILES=[
 "cybernetic09h/HOST_ATTESTATION_SCHEMA.json",
 "cybernetic09h/run_host_witness.py",
 "cybernetic09h/README.md",
 "tools/build_host_witness_pack09h.py",
 "tests/test_cybernetic09h.py",
 "tools/validate_cybernetic09h.py",
 "publication/SLICE_09H_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    receipt=json.loads((ROOT/"publication/SLICE_09H_RECEIPT.json").read_text())
    w=build_witness(host_id="chatgpt-codex",attestation=None,telemetry=[],candidates=[],adapter_version="validator")
    if w["witness_origin"]!="REFERENCE_IMPLEMENTATION":
        errors.append("runner self-certified live origin")
    if classify_witness(w)["status"]!="HOLD_NON_LIVE_WITNESS":
        errors.append("reference runner closed live gate")
    if receipt.get("live_host_witness_obtained") is not False:
        errors.append("slice must not claim live host witness")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_HOST_WITNESS_RUNNER_PACK_SLICE_09H",
      "default_origin":w["witness_origin"],
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "live_host_witness_obtained":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
