#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from cybernetic09d.crystallizer import propose_policy_update,rank_admissible,POLICY
from cybernetic09e.governor import promote,digest,policy_digest

PREVIOUS="adb4ccf266e8a7d59010b53dbafe4654a3e07dad6f2306986ca464a73c2c3936"
FILES=[
 "cybernetic09e/PROMOTION_POLICY.json",
 "cybernetic09e/ACTIVE_POLICY_REGISTRY.json",
 "cybernetic09e/governor.py",
 "tests/test_cybernetic09e.py",
 "tools/validate_cybernetic09e.py",
 "publication/SLICE_09E_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    registry=json.loads((ROOT/"cybernetic09e/ACTIVE_POLICY_REGISTRY.json").read_text())
    gov=json.loads((ROOT/"cybernetic09e/PROMOTION_POLICY.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09E_RECEIPT.json").read_text())
    telemetry=json.loads((ROOT/"cybernetic09d/REFERENCE_TELEMETRY.json").read_text())["records"]
    candidates=[
      {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
      {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"}
    ]
    current=copy.deepcopy(POLICY)
    proposal=propose_policy_update(telemetry,current)["proposal"]
    ranked=rank_admissible(candidates,telemetry,proposal)
    witness={"policy_digest":ranked["policy_digest"],"routing_order":ranked["routing_order"],"summary_digest":digest(ranked["summary"])}
    auth={"authorization_id":"validator-synthetic","principal_id":"validator","authority_level":"A3","rights":["POLICY_PROMOTE"],"proposal_digest":policy_digest(proposal),"predecessor_policy_digest":policy_digest(current)}
    promoted,result=promote(registry,current,proposal,telemetry,candidates,witness,auth)
    if result.get("status")!="PROMOTED":
        errors.append("governed promotion vector failed")
    if promoted["active_policy"]["policy_version"]!=2:
        errors.append("active policy version mismatch")
    if registry["active_policy"]["policy_version"]!=1:
        errors.append("live registry mutated by validator")
    if gov.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_POLICY_PROMOTION_AND_REPLAY_GOVERNOR_SLICE_09E",
      "live_active_policy_version":registry["active_policy"]["policy_version"],
      "synthetic_promoted_version":promoted["active_policy"]["policy_version"],
      "promotion_vector":"SYNTHETIC_TEST_ONLY",
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
