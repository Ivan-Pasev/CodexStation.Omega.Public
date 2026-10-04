#!/usr/bin/env python3
import hashlib, json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def build_sets():
    return {
        "objects":[x["id"] for x in load("registry/objectization04/OBJECTS.json")["objects"]],
        "skills":[x["id"] for x in load("registry/objectization04/SKILLS.json")["skills"]],
        "theorematic_objects":[x["theorem_id"] for x in load("registry/objectization04/THEOREM_DEPENDENCIES.json")["dependencies"]],
        "negative_hold_classes":[x["id"] for x in load("registry/objectization04/NEGATIVE_HOLD.json")["classes"]],
        "anchors":[x["id"] for x in load("registry/OMEGA_REGISTRY.json")["anchors"]],
    }

def fp(sets):
    data={k:sorted(v) for k,v in sets.items()}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def main():
    sets=build_sets()
    parent=load("distribution05/SEMANTIC_PARENT.json")
    compiled=load("distribution05/COMPILED_SEMANTICS.json")
    chat=load("dist/chatgpt-codex/DISTRIBUTION.json")
    gem=load("dist/gemini-notebook/DISTRIBUTION.json")
    receipt=load("publication/SLICE_04_RECEIPT.json")
    errors=[]

    if parent["semantic_parent_fingerprint"]!=receipt["objectization_fingerprint"]:
        errors.append("parent fingerprint differs from validated objectization")
    if compiled["parity_fingerprint"]!=fp(sets):
        errors.append("compiled parity fingerprint mismatch")
    expected_counts={k:len(v) for k,v in sets.items()}
    if compiled["counts"]!=expected_counts:
        errors.append("compiled counts mismatch")

    for name,dist in [("chatgpt",chat),("gemini",gem)]:
        if dist["semantic_parent_fingerprint"]!=parent["semantic_parent_fingerprint"]:
            errors.append(name+" parent mismatch")
        if dist.get("authority_delta")!="NONE":
            errors.append(name+" authority delta")
        if dist.get("release_eligible") is not False:
            errors.append(name+" release state")
        for key,expected in sets.items():
            actual=dist.get("semantic_sets",{}).get(key,[])
            if set(actual)!=set(expected) or len(actual)!=len(expected):
                errors.append(name+" semantic set mismatch: "+key)

    if chat["semantic_parent_fingerprint"]!=gem["semantic_parent_fingerprint"]:
        errors.append("provider parent divergence")

    report={
        "result":"PASS" if not errors else "FAIL",
        "semantic_parent_fingerprint":parent["semantic_parent_fingerprint"],
        "parity_fingerprint":fp(sets),
        "counts":expected_counts,
        "authority_delta":"NONE",
        "errors":errors
    }
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
