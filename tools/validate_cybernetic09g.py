#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from cybernetic09g.conformance import classify_witness,aggregate,expected_profile_digest

PREVIOUS="9fa495721064479fcb4bfa397e28ef7db62d510f817305e970b1c932bcf01424"
FILES=[
 "cybernetic09g/HOST_WITNESS_SCHEMA.json",
 "cybernetic09g/LIVE_CONFORMANCE_REGISTRY.json",
 "cybernetic09g/conformance.py",
 "tests/test_cybernetic09g.py",
 "tools/validate_cybernetic09g.py",
 "publication/SLICE_09G_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    registry=json.loads((ROOT/"cybernetic09g/LIVE_CONFORMANCE_REGISTRY.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09G_RECEIPT.json").read_text())
    if aggregate(registry)["status"]!="HOLD_NO_COMPLETE_LIVE_HOST_WITNESSES":
        errors.append("initial live registry must remain held")
    synthetic={
      "schema":"GILC/CODEXSTATION/OMEGA-LIVE-HOST-WITNESS/0.9g",
      "host_id":"chatgpt-codex",
      "host_profile_digest":expected_profile_digest("chatgpt-codex"),
      "active_policy_digest":registry["active_policy_digest"],
      "policy_version":1,
      "replay_policy_digest":registry["active_policy_digest"],
      "routing_order":[],
      "summary_digest":"synthetic",
      "environment":{"runtime":"validator","runtime_version":"1","adapter_version":"1","capability_observations":[]},
      "witness_origin":"SYNTHETIC_TEST",
      "execution_id":"synthetic",
      "status":"PASS"
    }
    if classify_witness(synthetic)["status"]!="HOLD_NON_LIVE_WITNESS":
        errors.append("synthetic witness improperly closes live gate")
    if receipt.get("live_host_conformance_closed") is not False:
        errors.append("slice receipt must not claim live conformance")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_HOST_WITNESS_AND_CONFORMANCE_GATE_SLICE_09G",
      "registry_state":aggregate(registry),
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "live_host_conformance_closed":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
