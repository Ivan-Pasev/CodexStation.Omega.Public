#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from cybernetic09b.compiler import compile_plan,execute_plan
from runtime08c.runtime import make_state

PREVIOUS="69f15615e127194a801aa3f92913678461cbcd136e9fbb0eddc3688be6421102"
FILES=[
 "cybernetic09b/MISSION_PLAN_SCHEMA.json",
 "cybernetic09b/EFFECT_GATE_POLICY.json",
 "cybernetic09b/compiler.py",
 "cybernetic09b/REFERENCE_MISSIONS.json",
 "tests/test_cybernetic09b.py",
 "tools/validate_cybernetic09b.py",
 "publication/SLICE_09B_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    schema=json.loads((ROOT/"cybernetic09b/MISSION_PLAN_SCHEMA.json").read_text())
    policy=json.loads((ROOT/"cybernetic09b/EFFECT_GATE_POLICY.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09B_RECEIPT.json").read_text())
    if "CAPABILITY_BINDING_DOES_NOT_CREATE_AUTHORITY" not in schema.get("laws",[]):
        errors.append("capability/authority noncollapse missing")
    if policy.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    st=make_state(project_id="v",grants=[{"grant_id":"g","principal_id":"actor","level":"A0","rights":[],"scope":["*"]}])
    mission={"id":"v.local","intent":"validate","mode":"LOCAL_VERIFICATION","required_capabilities":["cap.execute.public_ci"],"required_authority":["A0"]}
    plan=compile_plan(mission,project_id="v",principal_id="actor",local_operations=[{"op":"SET","key":"validated","value":True}],protected_invariants=["inv"],reversibility="REVERSIBLE")
    result=execute_plan(plan,state=st,capability_state={"cap.execute.public_ci":"OBSERVED"},grants=["A0"],invariant_results=[{"invariant_id":"inv","status":"PASS","evidence_refs":["validator"]}])
    if result.get("status")!="PASS":
        errors.append("local constitutional execution failed")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_MISSION_COMPILER_AND_EFFECT_GATE_SLICE_09B",
      "local_execution":result.get("status"),
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
