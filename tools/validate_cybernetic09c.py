#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from cybernetic09c.orchestrator import orchestrate
from runtime08c.runtime import make_state

PREVIOUS="bda8728a88b61a89781c6f0ae070ddfccb57bfc463a2191bcb3f8a2acb314501"
FILES=[
 "cybernetic09c/SKILL_REGISTRY.json",
 "cybernetic09c/ORCHESTRATION_POLICY.json",
 "cybernetic09c/orchestrator.py",
 "cybernetic09c/REFERENCE_WORKFLOWS.json",
 "tests/test_cybernetic09c.py",
 "tools/validate_cybernetic09c.py",
 "publication/SLICE_09C_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    registry=json.loads((ROOT/"cybernetic09c/SKILL_REGISTRY.json").read_text())
    policy=json.loads((ROOT/"cybernetic09c/ORCHESTRATION_POLICY.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09C_RECEIPT.json").read_text())
    if registry.get("law")!="SKILL_AVAILABLE != SKILL_QUALIFIED":
        errors.append("skill qualification firewall missing")
    if policy.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    st=make_state(project_id="v09c",grants=[{"grant_id":"g","principal_id":"actor","level":"A3","rights":[],"scope":["*"]}])
    steps=[
      {"step_id":"audit","intent":"source audit","skill_uri":"cs.skill::source-audit::v0.1","depends_on":[],"required_capabilities":["cap.observe.public_repo"],"required_authority":["A0"],"mode":"LOCAL_VERIFICATION"},
      {"step_id":"mutate","intent":"repository mutation","skill_uri":"cs.skill::repository-mutation::v0.1","depends_on":["audit"],"required_capabilities":["cap.mutate.public_repo"],"required_authority":["A2"],"mode":"LOCAL_VERIFICATION","local_operations":[{"op":"SET","key":"validated","value":True}],"reversibility":"REVERSIBLE"}
    ]
    result=orchestrate(project_id="v09c",principal_id="actor",steps=steps,state=st,capability_state={"cap.observe.public_repo":"OBSERVED","cap.mutate.public_repo":"OBSERVED"},grants=["A0","A2","A3"])
    if result.get("status")!="PASS" or result.get("state",{}).get("payload",{}).get("validated") is not True:
        errors.append("reference orchestration failed")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_SKILL_BINDER_AND_RECOVERY_ORCHESTRATOR_SLICE_09C",
      "workflow_status":result.get("status"),
      "step_status":result.get("step_status"),
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
