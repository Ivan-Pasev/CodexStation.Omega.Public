#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INCLUDE=[
 "runner08h/FAMILY_PROFILES.json",
 "runner08h/run_source.py",
 "runner08h/README.md",
 "bridge08f/EXPECTED_PINS.json",
 "bridge08f/RECEIPT_SCHEMA.json",
 "tools/verify_private_receipt08f.py",
 "ingestion08g/INGESTION_POLICY.json",
 "ingestion08g/ingest.py",
]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="build/runner08h")
    args=ap.parse_args()
    out=(ROOT/args.out)
    out.mkdir(parents=True,exist_ok=True)
    stage=out/"codexstation-omega-runner-v0.8h"
    if stage.exists():
        shutil.rmtree(stage)
    for rel in INCLUDE:
        src=ROOT/rel; dst=stage/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
    manifest={
      "schema":"GILC/CODEXSTATION/OMEGA-RUNNER-DISTRIBUTION/0.8h",
      "runner_pack_id":"cs.runner-pack::tier-a::v0.8h",
      "files":INCLUDE,
      "authority_delta":"NONE",
      "contains_restricted_source":False
    }
    (stage/"RUNNER_PACK_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    zip_path=out/"codexstation-omega-runner-v0.8h.zip"
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p,p.relative_to(stage))
    digest=hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(json.dumps({"result":"PASS","path":str(zip_path.relative_to(ROOT)),"sha256":digest,"file_count":len(INCLUDE)+1,"contains_restricted_source":False},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
