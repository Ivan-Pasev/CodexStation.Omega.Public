#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, subprocess, sys, tempfile, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
FIXED_DT=(2026,10,5,0,0,0)
PREVIOUS="cf9bc1de879c91756640cc145538324787646868811fa8ca9007e363b11c7de3"

def load(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def fps():
    p=subprocess.run([sys.executable,str(ROOT/"tools/validate_runtime08c.py")],capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stdout+p.stderr)
    r=json.loads(p.stdout)
    return r["slice_fingerprint"],r["composite_semantic_fingerprint"]

def one(spec_rel,out):
    spec=load(spec_rel); s,c=fps(); errors=[]
    if spec.get("previous_composite_semantic_fingerprint")!=PREVIOUS: errors.append("previous composite")
    if spec.get("authority_delta")!="NONE" or spec.get("release_eligible") is not False: errors.append("boundary")
    dests=[]
    for src,dst in spec.get("package_sources",[]):
        if not (ROOT/src).is_file(): errors.append("missing "+src)
        dests.append(dst)
    if len(dests)!=len(set(dests)): errors.append("duplicate destination")
    if errors: return {"result":"FAIL","errors":errors}
    out.mkdir(parents=True,exist_ok=True)
    zp=out/(spec["root_name"]+".zip")
    rows=[]
    with zipfile.ZipFile(zp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for src,dst in sorted(spec["package_sources"],key=lambda x:x[1]):
            payload=(ROOT/src).read_bytes()
            arc=spec["root_name"]+"/"+dst
            info=zipfile.ZipInfo(arc,FIXED_DT)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            zf.writestr(info,payload)
            rows.append({"source":src,"path":dst,"bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest()})
        manifest={
          "schema":"GILC/CODEXSTATION/OMEGA-PUBLIC-PACKAGE-RECEIPT/0.8c",
          "package_id":spec["package_id"],
          "profile":spec["profile"],
          "version":spec["version"],
          "slice_fingerprint":s,
          "composite_semantic_fingerprint":c,
          "files":rows,
          "release_eligible":False,
          "live_conformance":"OPEN",
          "authority_delta":"NONE"
        }
        raw=(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode()
        info=zipfile.ZipInfo(spec["root_name"]+"/PACKAGE_MANIFEST.json",FIXED_DT)
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        zf.writestr(info,raw)
    return {
      "result":"PASS","package_id":spec["package_id"],"profile":spec["profile"],
      "path":str(zp),"bytes":zp.stat().st_size,"sha256":sha(zp),
      "file_count":len(rows)+1,"slice_fingerprint":s,
      "composite_semantic_fingerprint":c,"authority_delta":"NONE"
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default=None); a=ap.parse_args()
    out=pathlib.Path(a.out) if a.out else pathlib.Path(tempfile.mkdtemp(prefix="omega08c_"))
    reports=[
      one("packaging08c/chatgpt-plugin/PACKAGING.json",out),
      one("packaging08c/gemini-notebook/PACKAGING.json",out)
    ]
    ok=all(x["result"]=="PASS" for x in reports)
    ok=ok and len({x.get("composite_semantic_fingerprint") for x in reports})==1
    print(json.dumps({"result":"PASS" if ok else "FAIL","packages":reports,"authority_delta":"NONE"},indent=2))
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
