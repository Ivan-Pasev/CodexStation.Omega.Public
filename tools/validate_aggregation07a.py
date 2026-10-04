#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"registry"/"aggregation07a"

def load(name):
    return json.loads((BASE/name).read_text(encoding="utf-8"))

def main():
    errors=[]
    schema=load("OMEGA_AGGREGATION_SCHEMA_BUNDLE.json")
    capsule=load("FAB_SYS_PROJECT_HARVEST_CAPSULE.json")
    holo=load("HOLOTOPE_SOVEREIGN_DIGITAL_RUNTIME_CORE.json")
    plate=load("PLATE_CODEXSTATION_EXECUTION_KNOWLEDGE_FABRIC.json")
    kernels=load("KERNEL_REGISTRY_SEED.json")

    for label,doc in [("schema",schema),("capsule",capsule),("holotope",holo),("plate",plate),("kernels",kernels)]:
        if doc.get("authority_delta")!="NONE":
            errors.append(label+": authority_delta must be NONE")

    if capsule.get("project_id")!="cs://project/fab-sys/root@2026-10-04":
        errors.append("unexpected FAB.SYS project id")
    if not capsule.get("source_roots"):
        errors.append("capsule missing source roots")
    if not capsule.get("open_gates"):
        errors.append("capsule must preserve open gates")

    if holo.get("semantic_parent")!="cs.semantic-parent::public-objectization-04::v0.5":
        errors.append("holotope semantic parent mismatch")
    if len(holo.get("kernels",[]))<5:
        errors.append("holotope kernel set too small")

    selected={x for x in plate.get("selected_methods_kernels",[])}
    if not selected.issubset(set(holo.get("kernels",[]))):
        errors.append("plate selected kernel not in holotope")
    if not plate.get("verification_plan"):
        errors.append("plate missing verification plan")

    ids=[x["id"] for x in kernels.get("kernels",[])]
    if len(ids)!=len(set(ids)):
        errors.append("duplicate kernel ids")
    if len(ids)<8:
        errors.append("kernel seed too small")
    if any(x.get("status","").startswith("SOURCE_BOUND")==False for x in kernels.get("kernels",[])):
        errors.append("kernel seed contains unbound kernel")

    payload=b"".join((BASE/n).read_bytes() for n in [
        "OMEGA_AGGREGATION_SCHEMA_BUNDLE.json",
        "FAB_SYS_PROJECT_HARVEST_CAPSULE.json",
        "HOLOTOPE_SOVEREIGN_DIGITAL_RUNTIME_CORE.json",
        "PLATE_CODEXSTATION_EXECUTION_KNOWLEDGE_FABRIC.json",
        "KERNEL_REGISTRY_SEED.json",
    ])
    report={
        "result":"PASS" if not errors else "FAIL",
        "aggregation_fingerprint":hashlib.sha256(payload).hexdigest(),
        "kernel_records":len(ids),
        "holotope_kernels":len(holo.get("kernels",[])),
        "capsule_open_gates":len(capsule.get("open_gates",[])),
        "authority_delta":"NONE",
        "errors":errors
    }
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
