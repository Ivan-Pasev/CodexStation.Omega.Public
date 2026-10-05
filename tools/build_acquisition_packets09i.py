#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from cybernetic09i.acquisition import make_request
HOSTS=["chatgpt-codex","gemini-notebook"]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="build/acquisition09i"); args=ap.parse_args()
    out=ROOT/args.out; out.mkdir(parents=True,exist_ok=True)
    requests={h:make_request(h) for h in HOSTS}
    for h,r in requests.items():
        (out/f"{h}.request.json").write_text(json.dumps(r,indent=2)+"\n")
    z=out/"codexstation-omega-live-host-acquisition-v0.9i.zip"
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as f:
        for h in HOSTS: f.write(out/f"{h}.request.json",f"{h}.request.json")
        for rel in ["cybernetic09h/run_host_witness.py","cybernetic09h/HOST_ATTESTATION_SCHEMA.json","cybernetic09g/HOST_WITNESS_SCHEMA.json"]:
            f.write(ROOT/rel,rel)
    print(json.dumps({"result":"PASS","path":str(z.relative_to(ROOT)),"sha256":hashlib.sha256(z.read_bytes()).hexdigest(),"host_requests":HOSTS,"live_receipts_included":False},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
