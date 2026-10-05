#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from cybernetic09d.crystallizer import summarize,rank_admissible,replay,POLICY

PREVIOUS="e6666396426c2922bc68fc6256e75f7c7477f69027aa7fa43b9cb43037a579ee"
FILES=[
 "cybernetic09d/TELEMETRY_SCHEMA.json",
 "cybernetic09d/ADAPTIVE_POLICY.json",
 "cybernetic09d/crystallizer.py",
 "cybernetic09d/REFERENCE_TELEMETRY.json",
 "tests/test_cybernetic09d.py",
 "tools/validate_cybernetic09d.py",
 "publication/SLICE_09D_RECEIPT.json"
]

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    telemetry=json.loads((ROOT/"cybernetic09d/REFERENCE_TELEMETRY.json").read_text())["records"]
    schema=json.loads((ROOT/"cybernetic09d/TELEMETRY_SCHEMA.json").read_text())
    policy=json.loads((ROOT/"cybernetic09d/ADAPTIVE_POLICY.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_09D_RECEIPT.json").read_text())
    if "SUCCESS_RATE != QUALIFICATION" not in schema.get("laws",[]):
        errors.append("qualification firewall missing")
    if policy.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    candidates=[
      {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
      {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"}
    ]
    ranked=rank_admissible(candidates,telemetry,policy)
    if ranked["routing_order"]!=["cs.skill::source-audit::v0.1","cs.skill::adversarial-review::v0.1"]:
        errors.append("adaptive ranking mismatch")
    if not replay(telemetry,candidates,policy)["deterministic"]:
        errors.append("policy replay nondeterministic")
    sf,cf=fingerprint()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "slice":"OMEGA_CYBERNETIC_ADAPTIVE_POLICY_AND_TELEMETRY_CRYSTALLIZATION_SLICE_09D",
      "routing_order":ranked["routing_order"],
      "health":{k:v["health"] for k,v in ranked["summary"].items()},
      "policy_version":policy["policy_version"],
      "policy_digest":ranked["policy_digest"],
      "slice_fingerprint":sf,
      "composite_semantic_fingerprint":cf,
      "authority_delta":"NONE",
      "release_eligible":False,
      "errors":errors
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
