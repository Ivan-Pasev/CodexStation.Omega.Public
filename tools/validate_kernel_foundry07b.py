#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"kernel-foundry07b"

def load(name):
    return json.loads((BASE/name).read_text(encoding="utf-8"))

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def main():
    errors=[]
    ledger=load("SOURCE_LEDGER.json")
    kernels=load("KERNEL_REGISTRY.json")
    abi=load("SOVEREIGN_RUNTIME_ABI.json")
    matrix=load("COMPATIBILITY_MATRIX.json")
    ext=load("SEMANTIC_EXTENSION.json")

    for label,doc in [("ledger",ledger),("kernels",kernels),("abi",abi),("matrix",matrix),("extension",ext)]:
        if doc.get("authority_delta")!="NONE":
            errors.append(f"{label}: authority_delta must be NONE")

    source_ids=[x.get("id") for x in ledger.get("sources",[])]
    if len(source_ids)!=len(set(source_ids)):
        errors.append("duplicate source IDs")
    source_set=set(source_ids)
    for s in ledger.get("sources",[]):
        if not s.get("repo") or not s.get("path") or not s.get("sha"):
            errors.append(f"incomplete source ledger entry: {s.get('id')}")
        if len(str(s.get("sha","")))!=40:
            errors.append(f"source SHA must be git SHA1 length 40: {s.get('id')}")

    ks=kernels.get("kernels",[])
    if len(ks)!=14:
        errors.append(f"expected 14 kernels, got {len(ks)}")
    kids=[x.get("kernel_id") for x in ks]
    if len(kids)!=len(set(kids)):
        errors.append("duplicate kernel IDs")
    aliases={x.get("alias") for x in ks}
    if aliases!={f"K{i}" for i in range(14)}:
        errors.append("kernel aliases must be exactly K0..K13")
    for k in ks:
        if not k.get("source_refs"):
            errors.append(f"kernel has no source refs: {k.get('kernel_id')}")
        for sid in k.get("source_refs",[]):
            if sid not in source_set:
                errors.append(f"unknown source ref {sid} in {k.get('kernel_id')}")
        if not k.get("authority_ceiling"):
            errors.append(f"kernel missing authority ceiling: {k.get('kernel_id')}")
        if "known_failures" not in k:
            errors.append(f"kernel missing failure modes: {k.get('kernel_id')}")

    records=abi.get("records",[])
    if len(records)!=10:
        errors.append(f"expected 10 ABI records, got {len(records)}")
    aids=[x.get("abi_id") for x in records]
    if len(aids)!=len(set(aids)):
        errors.append("duplicate ABI IDs")
    for rec in records:
        if not rec.get("required") or not rec.get("laws") or not rec.get("adapters"):
            errors.append(f"incomplete ABI record: {rec.get('abi_id')}")

    systems=matrix.get("systems",[])
    if len(systems)<9:
        errors.append("compatibility matrix must cover at least nine systems")
    allowed={"DIRECT","ADAPTER","PARTIAL","NONE_OBSERVED"}
    axes=["identity","transition","authority","invariants","event_replay","witness_receipt","rollback","knowledge_admission","conflict","execution","projection","release"]
    for sys in systems:
        for axis in axes:
            if sys.get(axis) not in allowed:
                errors.append(f"bad compatibility class {sys.get('system')}:{axis}={sys.get(axis)}")

    if ext.get("base_composite_semantic_fingerprint")!="daa85b0bf47e392c4a310b2dc11f8074dee2480b5b7dd34c3bde917981bd4c7d":
        errors.append("07A base composite fingerprint mismatch")
    if set(ext.get("kernel_ids",[]))!=set(kids):
        errors.append("extension kernel IDs differ from registry")
    if set(ext.get("abi_ids",[]))!=set(aids):
        errors.append("extension ABI IDs differ from ABI registry")
    if ext.get("release_eligible") is not False:
        errors.append("release_eligible must remain false")

    fp_payload={
        "source_ledger":ledger,
        "kernel_registry":kernels,
        "abi":abi,
        "compatibility":matrix
    }
    ext_fp=hashlib.sha256(canonical(fp_payload)).hexdigest()
    composite=hashlib.sha256((
        ext["base_composite_semantic_fingerprint"]+":"+ext_fp
    ).encode("utf-8")).hexdigest()

    report={
        "result":"PASS" if not errors else "FAIL",
        "source_records":len(source_ids),
        "kernels":len(ks),
        "abi_records":len(records),
        "systems":len(systems),
        "kernel_foundry_extension_fingerprint":ext_fp,
        "composite_semantic_fingerprint":composite,
        "authority_delta":"NONE",
        "errors":errors,
        "does_not_establish":[
            "cross-repository runtime integration",
            "production readiness",
            "formal theoremhood",
            "empirical confirmation",
            "live provider conformance",
            "release eligibility"
        ]
    }
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
