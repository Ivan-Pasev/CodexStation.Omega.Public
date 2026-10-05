#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INCLUDE=[
 "cybernetic09h/HOST_ATTESTATION_SCHEMA.json",
 "cybernetic09h/run_host_witness.py",
 "cybernetic09h/README.md",
 "cybernetic09g/HOST_WITNESS_SCHEMA.json",
 "cybernetic09g/conformance.py",
 "cybernetic09f/HOST_PROFILES.json",
 "cybernetic09f/distributor.py",
 "cybernetic09e/ACTIVE_POLICY_REGISTRY.json",
 "cybernetic09d/ADAPTIVE_POLICY.json",
 "cybernetic09d/crystallizer.py",
 "cybernetic09d/REFERENCE_TELEMETRY.json"
]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="build/host-witness09h")
    args=ap.parse_args()
    out=ROOT/args.out
    out.mkdir(parents=True,exist_ok=True)
    stage=out/"codexstation-omega-host-witness-v0.9h"
    if stage.exists(): shutil.rmtree(stage)
    for rel in INCLUDE:
        src=ROOT/rel; dst=stage/rel
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    manifest={
      "schema":"GILC/CODEXSTATION/OMEGA-HOST-WITNESS-DISTRIBUTION/0.9h",
      "files":INCLUDE,
      "contains_private_source":False,
      "live_origin_self_certification":False,
      "authority_delta":"NONE"
    }
    (stage/"HOST_WITNESS_PACK_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    zpath=out/"codexstation-omega-host-witness-v0.9h.zip"
    with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file(): z.write(p,p.relative_to(stage))
    print(json.dumps({"result":"PASS","path":str(zpath.relative_to(ROOT)),"sha256":hashlib.sha256(zpath.read_bytes()).hexdigest(),"file_count":len(INCLUDE)+1,"contains_private_source":False},indent=2))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
