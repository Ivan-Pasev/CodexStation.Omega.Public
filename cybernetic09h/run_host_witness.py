#!/usr/bin/env python3
"""Portable host witness runner for CodexStation Omega v0.9h."""
from __future__ import annotations
import argparse, json, platform, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cybernetic09d.crystallizer import POLICY, replay
from cybernetic09f.distributor import HOSTS, host_profile_digest, digest
from cybernetic09g.conformance import EXPECTED_POLICY

REFERENCE_TELEMETRY=json.loads((ROOT/"cybernetic09d/REFERENCE_TELEMETRY.json").read_text())["records"]
REFERENCE_CANDIDATES=[
 {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
 {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"}
]

def load_json(path:str|None):
    return json.loads(Path(path).read_text()) if path else None

def classify_origin(host_id:str, attestation:dict|None)->tuple[str,list[str],str]:
    reasons=[]
    if attestation is None:
        return "REFERENCE_IMPLEMENTATION",["NO_HOST_ATTESTATION"],"reference"
    if attestation.get("host_id")!=host_id:
        reasons.append("ATTESTATION_HOST_ID_MISMATCH")
    if attestation.get("host_profile_digest")!=host_profile_digest(host_id):
        reasons.append("ATTESTATION_PROFILE_DIGEST_MISMATCH")
    if attestation.get("attestation_class")!="HOST_BOUND_RUNTIME":
        reasons.append("ATTESTATION_CLASS_NOT_HOST_BOUND")
    if not attestation.get("runtime_channel"):
        reasons.append("RUNTIME_CHANNEL_MISSING")
    if not attestation.get("execution_id"):
        reasons.append("EXECUTION_ID_MISSING")
    if not attestation.get("evidence_refs"):
        reasons.append("EVIDENCE_REFS_MISSING")
    if reasons:
        return "REFERENCE_IMPLEMENTATION",reasons,"reference"
    return "LIVE_HOST",[],"host-bound-attestation"

def build_witness(*,host_id:str,attestation:dict|None,telemetry:list[dict],candidates:list[dict],adapter_version:str)->dict:
    if host_id not in HOSTS:
        raise ValueError("unknown host")
    rr=replay(telemetry,candidates,POLICY)
    result=rr["result"]
    origin,reasons,origin_basis=classify_origin(host_id,attestation)
    execution_id=(attestation or {}).get("execution_id") or "reference-local"
    env={
      "runtime":platform.python_implementation(),
      "runtime_version":platform.python_version(),
      "adapter_version":adapter_version,
      "capability_observations":HOSTS[host_id]["capability_profile"],
      "origin_basis":origin_basis,
      "origin_reasons":reasons
    }
    witness={
      "schema":"GILC/CODEXSTATION/OMEGA-LIVE-HOST-WITNESS/0.9g",
      "host_id":host_id,
      "host_profile_digest":host_profile_digest(host_id),
      "active_policy_digest":EXPECTED_POLICY,
      "policy_version":1,
      "replay_policy_digest":result["policy_digest"],
      "routing_order":result["routing_order"],
      "summary_digest":digest(result["summary"]),
      "environment":env,
      "witness_origin":origin,
      "execution_id":execution_id,
      "status":"PASS" if rr["deterministic"] and result["policy_digest"]==EXPECTED_POLICY else "UNKNOWN_OUTCOME"
    }
    if attestation is not None:
        witness["origin_attestation_digest"]=digest(attestation)
        witness["origin_evidence_refs"]=list(attestation.get("evidence_refs",[]))
    return witness

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--host-id",required=True,choices=sorted(HOSTS))
    ap.add_argument("--attestation")
    ap.add_argument("--telemetry")
    ap.add_argument("--candidates")
    ap.add_argument("--adapter-version",default="omega-09h")
    ap.add_argument("--out")
    args=ap.parse_args()
    att=load_json(args.attestation)
    telemetry=load_json(args.telemetry) or REFERENCE_TELEMETRY
    candidates=load_json(args.candidates) or REFERENCE_CANDIDATES
    if isinstance(candidates,dict) and "candidates" in candidates:
        candidates=candidates["candidates"]
    w=build_witness(host_id=args.host_id,attestation=att,telemetry=telemetry,candidates=candidates,adapter_version=args.adapter_version)
    data=json.dumps(w,indent=2)+"\n"
    if args.out:
        Path(args.out).write_text(data)
    else:
        sys.stdout.write(data)
    return 0 if w["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
