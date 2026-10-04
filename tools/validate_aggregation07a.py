#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def canonical_hash(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def main():
    errors=[]
    ext=load("aggregation07a/SEMANTIC_EXTENSION.json")
    schema=load("aggregation07a/SCHEMA_BUNDLE.json")
    atlas=load("aggregation07a/INITIAL_PUBLIC_KERNEL_ATLAS.json")
    manifest=load("MANIFEST.json")

    if ext.get("authority_delta")!="NONE":
        errors.append("extension authority_delta must be NONE")
    if ext.get("release_eligible") is not False:
        errors.append("extension release_eligible must remain false")
    if atlas.get("authority_delta")!="NONE":
        errors.append("atlas authority_delta must be NONE")
    if manifest.get("release_eligible") is not False:
        errors.append("manifest release_eligible must remain false")

    defs=schema.get("$defs",{})
    required_defs={"ProjectHarvestCapsule","KernelRecord","Holotope","ArchetonicPlate"}
    missing=required_defs-set(defs)
    if missing:
        errors.append("missing schema defs: "+",".join(sorted(missing)))

    for name in required_defs:
        d=defs.get(name,{})
        props=d.get("properties",{})
        ad=props.get("authority_delta",{})
        if ad.get("const")!="NONE":
            errors.append(name+" must freeze authority_delta to NONE")

    repos=atlas.get("repositories",[])
    if len(repos)<10:
        errors.append("public kernel atlas too small")
    if len({r.get("repo") for r in repos})!=len(repos):
        errors.append("duplicate repository in public kernel atlas")

    open_gates=set(ext.get("parallel_open_gates",[]))
    for gate in ["NB00_LIVE_CONFORMANCE_01","RGT-04_BUNDLED_FALLBACK_CLEAN_CHAT","LICENSE_IP_REVIEW"]:
        if gate not in open_gates:
            errors.append("missing preserved open gate: "+gate)

    ext_hash=canonical_hash(ext)
    composite=hashlib.sha256((ext["base_semantic_parent_fingerprint"]+":"+ext_hash).encode()).hexdigest()

    report={
        "result":"PASS" if not errors else "FAIL",
        "base_semantic_parent_fingerprint":ext["base_semantic_parent_fingerprint"],
        "aggregation_extension_fingerprint":ext_hash,
        "composite_semantic_fingerprint":composite,
        "object_types":len(ext.get("object_types",[])),
        "public_kernel_repositories":len(repos),
        "kernel_families":len(atlas.get("kernel_families",[])),
        "authority_delta":"NONE",
        "errors":errors,
        "does_not_establish":[
            "live host conformance",
            "full private corpus publication",
            "formal theoremhood",
            "empirical confirmation",
            "release eligibility"
        ]
    }
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
