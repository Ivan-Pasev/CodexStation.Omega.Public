#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
FIXED_DT=(2026,10,4,0,0,0)
BASE_PARENT="eb43face6ab49b0eab112b5c9ddc6308a5dc0444c3d140622365c61976138719"
EXT="c74ce95fda667d384d95fc4852a932a2a5bdc242b0c819ab5012696988c9153a"
COMPOSITE="daa85b0bf47e392c4a310b2dc11f8074dee2480b5b7dd34c3bde917981bd4c7d"

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_one(spec_rel,out_dir):
    spec=load(spec_rel)
    errors=[]
    checks=[
        ("base_semantic_parent_fingerprint",BASE_PARENT),
        ("aggregation_extension_fingerprint",EXT),
        ("composite_semantic_fingerprint",COMPOSITE),
    ]
    for field,expected in checks:
        if spec.get(field)!=expected:
            errors.append(f"{field} mismatch")
    if spec.get("authority_delta")!="NONE":
        errors.append("authority_delta must be NONE")
    if spec.get("release_eligible") is not False:
        errors.append("release_eligible must remain false")

    mappings=spec.get("package_sources",[])
    dests=[]
    for src,dst in mappings:
        if not (ROOT/src).is_file():
            errors.append("missing source: "+src)
        dests.append(dst)
    if len(dests)!=len(set(dests)):
        errors.append("duplicate package destination")

    if errors:
        return {"result":"FAIL","errors":errors}

    out_dir.mkdir(parents=True,exist_ok=True)
    zip_path=out_dir/(spec["root_name"]+".zip")
    manifest_files=[]
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for src,dst in sorted(mappings,key=lambda x:x[1]):
            payload=(ROOT/src).read_bytes()
            arc=spec["root_name"]+"/"+dst
            info=zipfile.ZipInfo(arc,FIXED_DT)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            zf.writestr(info,payload)
            manifest_files.append({
                "source":src,
                "path":dst,
                "bytes":len(payload),
                "sha256":hashlib.sha256(payload).hexdigest()
            })

        package_manifest={
            "schema":"GILC/CODEXSTATION/OMEGA-PUBLIC-PACKAGE-RECEIPT/0.7a",
            "package_id":spec["package_id"],
            "profile":spec["profile"],
            "version":spec["version"],
            "base_semantic_parent_fingerprint":BASE_PARENT,
            "aggregation_extension_fingerprint":EXT,
            "composite_semantic_fingerprint":COMPOSITE,
            "files":manifest_files,
            "release_eligible":False,
            "live_conformance":"OPEN",
            "authority_delta":"NONE"
        }
        raw=(json.dumps(package_manifest,indent=2,sort_keys=True)+"\n").encode()
        info=zipfile.ZipInfo(spec["root_name"]+"/PACKAGE_MANIFEST.json",FIXED_DT)
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        zf.writestr(info,raw)

    return {
        "result":"PASS",
        "package_id":spec["package_id"],
        "profile":spec["profile"],
        "path":str(zip_path),
        "bytes":zip_path.stat().st_size,
        "sha256":sha256(zip_path),
        "file_count":len(manifest_files)+1,
        "base_semantic_parent_fingerprint":BASE_PARENT,
        "aggregation_extension_fingerprint":EXT,
        "composite_semantic_fingerprint":COMPOSITE,
        "authority_delta":"NONE"
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
