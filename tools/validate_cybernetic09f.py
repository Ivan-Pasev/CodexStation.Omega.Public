#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from cybernetic09f.distributor import distribute,compare_receipts
from cybernetic09d.crystallizer import POLICY

PREVIOUS="aa247cd65a8505bab2ec11b9bc470a1d42fb6d19c6c79c1ef4b05c890effe8f2"
FILES=[
 "cybernetic09f/HOST_PROFILES.json",
 "cybernetic09f/DISTRIBUTION_CONTRACT.json",
 "cybernetic09f/distributor.py",
 "tests/test_cybernetic09f.py",
 "tools/validate_cybernetic09f.py",
 "publication/SLICE_09F_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    reg=json.loads((ROOT/"cybernetic09e/ACTIVE_POLICY_REGISTRY.json").read_text())
    telemetry=json.loads((ROOT/"cybernetic09d/REFERENCE_TELEMETRY.json").read_text())["records"]
    receipt=json.loads((ROOT/"publication/SLICE_09F_RECEIPT.json").read_text())
    candidates=[
      {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
      {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"}
    ]
    host_receipts=[distribute(h,reg,POLICY,telemetry,candidates) for h in ("chatgpt-codex","gemini-notebook")]
    parity=compare_receipts(host_receipts)
    if parity.get("status")!="PARITY_PASS":
        errors.append("host parity failed")
    if len({x["host_profile_digest"] for x in host_receipts})!=2:
        errors.append("host profiles should differ")
    if len({x["active_policy_digest"] for x in host_receipts})!=1:
        errors.append("active policy digest diverged")
    if receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_MULTI_HOST_REPLAY_AND_POLICY_DISTRIBUTION_SLICE_09F",
      "hosts":[{"host_id":x["host_id"],"status":x["status"],"host_profile_digest":x["host_profile_digest"]} for x in host_receipts],
      "parity_status":parity["status"],
      "active_policy_digest":parity.get("policy_digest"),
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "live_host_execution_claimed":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
