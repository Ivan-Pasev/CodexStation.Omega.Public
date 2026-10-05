#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from cybernetic09a.controller import cycle

PREVIOUS="39db2bcb7652a6ee31bb796d2c8c37c3c93bd9a50c891693d23362c431bf49cb"
FILES=[
 "cybernetic09a/CAPABILITY_LATTICE.json",
 "cybernetic09a/CONTROL_POLICY.json",
 "cybernetic09a/FRONTIER_SEED.json",
 "cybernetic09a/controller.py",
 "tests/test_cybernetic09a.py",
 "tools/validate_cybernetic09a.py",
 "publication/SLICE_09A_RECEIPT.json"
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
    caps=json.loads((ROOT/"cybernetic09a/CAPABILITY_LATTICE.json").read_text())
    policy=json.loads((ROOT/"cybernetic09a/CONTROL_POLICY.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09A_RECEIPT.json").read_text())
    if caps.get("law")!="CAPABILITY_LEVEL != AUTHORITY_LEVEL":
        errors.append("capability/authority firewall missing")
    if policy.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    result=cycle(grants=["A0"])
    if result.get("status")!="VERIFIED":
        errors.append("default control cycle did not verify")
    if result.get("selection",{}).get("mission",{}).get("id")!="mission.09a.cybernetic-self-validation":
        errors.append("frontier selection law failed")
    held=[x["id"] for x in result.get("frontier",[]) if x["status"].startswith("HELD")]
    if "mission.08i.restricted-receipts" not in held:
        errors.append("08I evidence frontier must remain held")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_CONTROL_PLANE_SLICE_09A",
      "selected_mission":result.get("selection",{}).get("mission",{}).get("id"),
      "held_frontier":held,
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
