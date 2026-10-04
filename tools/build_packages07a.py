#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
FIXED_DT=(2026,10,4,0,0,0)
PARENT="eb43face6ab49b0eab112b5c9ddc6308a5dc0444c3d140622365c61976138719"
PARITY="7ebb3332e2596fc53a2f956bbe26bf558fa96a93c159d0190625d10993d3dcd1"

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_one(spec_rel,out_dir):
    spec=load(spec_rel)
    errors=[]
    if spec.get("authority_delta")!="NONE":
        errors.append("authority_delta")
    if spec.get("release_eligible") is not False:
        errors.append("release_eligible")
    if spec.get("semantic_parent_fingerprint")!=PARENT:
        errors.append("semantic parent")
    if spec.get("parity_fingerprint")!=PARITY:
        errors.append("parity")
    mappings=spec.get("package_sources",[])
    if len({dst for _,dst in mappings})!=len(mappings):
        errors.append("duplicate destinations")
    for src,_ in mappings:
        if not (ROOT/src).is_file():
            errors.append("missing "+src)
    if errors:
        return {"result":"FAIL","errors":errors}

    out_dir.mkdir(parents=True,exist_ok=True)
    zp=out_dir/(spec["root_name"]+".zip")
    manifest=[]
    with zipfile.ZipFile(zp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for src,dst in sorted(mappings,key=lambda x:x[1]):
            payload=(ROOT/src).read_bytes()
            arc=spec["root_name"]+"/"+dst
            info=zipfile.ZipInfo(arc,FIXED_DT)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            zf.writestr(info,payload)
            manifest.append({"source":src,"path":dst,"bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest()})
        pm={
            "schema":"GILC/CODEXSTATION/OMEGA-PUBLIC-PACKAGE-RECEIPT/0.7",
            "package_id":spec["package_id"],
            "profile":spec["profile"],
            "version":spec["version"],
            "semantic_parent_fingerprint":PARENT,
            "parity_fingerprint":PARITY,
            "files":manifest,
            "release_eligible":False,
            "authority_delta":"NONE"
        }
        raw=(json.dumps(pm,indent=2,sort_keys=True)+"\n").encode()
        info=zipfile.ZipInfo(spec["root_name"]+"/PACKAGE_MANIFEST.json",FIXED_DT)
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        zf.writestr(info,raw)
    return {
        "result":"PASS","package_id":spec["package_id"],"profile":spec["profile"],
        "path":str(zp),"bytes":zp.stat().st_size,"sha256":digest(zp),
        "file_count":len(manifest)+1,"semantic_parent_fingerprint":PARENT,
        "parity_fingerprint":PARITY,"authority_delta":"NONE"
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default=None)
    args=ap.parse_args()
    out=pathlib.Path(args.out) if args.out else pathlib.Path(tempfile.mkdtemp(prefix="omega_pkg07a_"))
    reports=[
        build_one("packaging07a/chatgpt-plugin/PACKAGING.json",out),
        build_one("packaging07a/gemini-notebook/PACKAGING.json",out)
    ]
    result="PASS" if all(x.get("result")=="PASS" for x in reports) else "FAIL"
    print(json.dumps({"result":result,"packages":reports,"authority_delta":"NONE"},indent=2))
    return 0 if result=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
