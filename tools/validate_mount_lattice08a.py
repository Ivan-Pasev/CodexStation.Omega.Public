#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
PREVIOUS="daa85b0bf47e392c4a310b2dc11f8074dee2480b5b7dd34c3bde917981bd4c7d"
SLICE_FILES=[
    "aggregation08a/SCHEMA_EXTENSION.json",
    "aggregation08a/MOUNT_REGISTRY.json",
    "aggregation08a/KERNEL_LATTICE.json",
    "aggregation08a/SEMANTIC_EXTENSION.json",
]
EVIDENCE_FIELDS=["SPEC","IMPLEMENTATION","TEST","CI","FORMAL","RUNTIME","EMPIRICAL","REPLICATION","RELEASE"]

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def canonical_bytes(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def fingerprints():
    h=hashlib.sha256()
    for rel in SLICE_FILES:
        h.update(canonical_bytes(load(rel)))
        h.update(b"\n")
    slice_fp=h.hexdigest()
    composite=hashlib.sha256((PREVIOUS+"|"+slice_fp).encode()).hexdigest()
    return slice_fp,composite

def main():
    errors=[]
    schema=load(SLICE_FILES[0])
    mounts=load(SLICE_FILES[1])
    lattice=load(SLICE_FILES[2])
    ext=load(SLICE_FILES[3])

    defs=schema.get("$defs",{})
    required_defs={"ProjectMount","HarvestSession","KnowledgeQuantum","LatticeAdmission","FeedbackPacket","KernelLatticeEntry"}
    if not required_defs.issubset(defs):
        errors.append("missing required schema defs")
    for name in required_defs:
        props=defs.get(name,{}).get("properties",{})
        if props.get("authority_delta",{}).get("const")!="NONE":
            errors.append(f"{name}: authority_delta not fixed to NONE")

    mount_ids=[x.get("mount_id") for x in mounts.get("mounts",[])]
    if len(mount_ids)!=len(set(mount_ids)):
        errors.append("duplicate mount ids")
    if len(mount_ids)<8:
        errors.append("expected at least 8 seed mounts")
    if mounts.get("authority_delta")!="NONE":
        errors.append("mount registry authority delta")

    kernel_ids=[x.get("kernel_id") for x in lattice.get("kernels",[])]
    if len(kernel_ids)!=len(set(kernel_ids)):
        errors.append("duplicate kernel ids")
    if len(kernel_ids)<18:
        errors.append("expected at least 18 kernel entries")
    for k in lattice.get("kernels",[]):
        ev=k.get("evidence_vector",{})
        if set(ev)!=set(EVIDENCE_FIELDS):
            errors.append(f"{k.get('kernel_id')}: incomplete evidence vector")
        if k.get("authority_delta")!="NONE":
            errors.append(f"{k.get('kernel_id')}: authority delta")
        if not k.get("source_refs"):
            errors.append(f"{k.get('kernel_id')}: missing source refs")
        if not k.get("revision_binding"):
            errors.append(f"{k.get('kernel_id')}: missing revision binding")
    if lattice.get("authority_delta")!="NONE":
        errors.append("kernel lattice authority delta")

    ext_kernel_ids=ext.get("kernel_ids",[])
    if set(ext_kernel_ids)!=set(kernel_ids):
        errors.append("semantic extension kernel set mismatch")
    if ext.get("previous_composite_semantic_fingerprint")!=PREVIOUS:
        errors.append("previous composite fingerprint mismatch")
    gates=set(ext.get("parallel_open_gates",[]))
    for required in ["NB00_LIVE_CONFORMANCE_01","RGT-04_BUNDLED_FALLBACK_CLEAN_CHAT","LICENSE_IP_REVIEW"]:
        if required not in gates:
            errors.append("missing open gate: "+required)
    if ext.get("release_eligible") is not False:
        errors.append("release_eligible must remain false")
    if ext.get("authority_delta")!="NONE":
        errors.append("semantic extension authority delta")

    slice_fp,composite=fingerprints()
    report={
        "result":"PASS" if not errors else "FAIL",
        "previous_composite_semantic_fingerprint":PREVIOUS,
        "slice_fingerprint":slice_fp,
        "composite_semantic_fingerprint":composite,
        "schema_defs":len(required_defs),
        "mounts":len(mount_ids),
        "kernels":len(kernel_ids),
        "conversation_derived_candidates":len(lattice.get("conversation_derived_candidates",[])),
        "authority_delta":"NONE",
        "errors":errors,
        "does_not_establish":[
            "live host conformance",
            "production readiness",
            "formal proof beyond source-reported scoped evidence",
            "empirical or scientific confirmation",
            "release eligibility"
        ]
    }
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
