#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "registry" / "objectization04"
REG = json.loads((ROOT / "registry" / "OMEGA_REGISTRY.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

def load(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))

def unique(items, key, label, errors):
    vals = [x.get(key) for x in items]
    if None in vals or "" in vals:
        errors.append(f"{label}: missing {key}")
    if len(vals) != len(set(vals)):
        errors.append(f"{label}: duplicate {key}")
    return set(vals)

def main():
    errors = []
    objects = load("OBJECTS.json")
    provenance = load("PROVENANCE.json")
    relations = load("RELATIONS.json")
    negative = load("NEGATIVE_HOLD.json")
    skills = load("SKILLS.json")
    theorem_deps = load("THEOREM_DEPENDENCIES.json")

    for label, doc in [
        ("objects", objects),
        ("provenance", provenance),
        ("relations", relations),
        ("negative", negative),
        ("skills", skills),
        ("theorem_deps", theorem_deps),
    ]:
        if doc.get("authority_delta") != "NONE":
            errors.append(f"{label}: authority_delta must be NONE")

    object_ids = unique(objects.get("objects", []), "id", "objects", errors)
    if len(object_ids) != 12:
        errors.append(f"expected 12 family objects, got {len(object_ids)}")

    source_map = json.loads((ROOT / "registry" / "metabolization03" / "SOURCES.json").read_text(encoding="utf-8"))
    source_ids = {x["id"] for x in source_map["sources"]}
    prov_objects = set()
    for mapping in provenance.get("mappings", []):
        oid = mapping.get("object_id")
        prov_objects.add(oid)
        if oid not in object_ids:
            errors.append(f"provenance object missing: {oid}")
        for sid in mapping.get("source_ids", []):
            if sid not in source_ids:
                errors.append(f"unknown source id: {sid}")
    if prov_objects != object_ids:
        errors.append("provenance coverage must equal object set")

    allowed_rel = set(REG.get("relation_types", []))
    unique(relations.get("relations", []), "id", "relations", errors)
    for rel in relations.get("relations", []):
        if rel.get("from") not in object_ids or rel.get("to") not in object_ids:
            errors.append(f"relation endpoint missing: {rel.get('id')}")
        if rel.get("type") not in allowed_rel:
            errors.append(f"relation type not in main registry: {rel.get('type')}")

    neg_ids = unique(negative.get("classes", []), "id", "negative classes", errors)
    required_neg = {
        "cs.negative::no-go::v0.4",
        "cs.negative::contradiction::v0.4",
        "cs.negative::hold::v0.4",
        "cs.negative::bounded-search::v0.4",
    }
    if not required_neg.issubset(neg_ids):
        errors.append("required negative/HOLD classes missing")

    skill_ids = unique(skills.get("skills", []), "id", "skills", errors)
    if len(skill_ids) < 12:
        errors.append("deep public spindle must contain at least 12 skills")
    for skill in skills.get("skills", []):
        if not skill.get("guards"):
            errors.append(f"skill missing guards: {skill.get('id')}")
        if not skill.get("required_capabilities"):
            errors.append(f"skill missing required capabilities: {skill.get('id')}")
        if not skill.get("method"):
            errors.append(f"skill missing method: {skill.get('id')}")

    theorem_ids = {x["id"] for x in REG.get("theorematic_objects", [])}
    dep_theorems = set()
    for item in theorem_deps.get("dependencies", []):
        tid = item.get("theorem_id")
        dep_theorems.add(tid)
        if tid not in theorem_ids:
            errors.append(f"unknown theorem dependency target: {tid}")
        for oid in item.get("depends_on", []):
            if oid not in object_ids:
                errors.append(f"theorem dependency object missing: {oid}")
        if not item.get("open_obligations"):
            errors.append(f"theorem dependency missing obligations: {tid}")
    if dep_theorems != theorem_ids:
        errors.append("theorem dependency coverage must equal theorem registry")

    if MANIFEST.get("release_eligible") is not False:
        errors.append("release_eligible must remain false")
    if MANIFEST.get("license_policy") != "OPEN_DECISION":
        errors.append("license policy must remain OPEN_DECISION")

    payload = b"".join((BASE / name).read_bytes() for name in [
        "OBJECTS.json","PROVENANCE.json","RELATIONS.json","NEGATIVE_HOLD.json",
        "SKILLS.json","THEOREM_DEPENDENCIES.json"
    ])
    report = {
        "result": "PASS" if not errors else "FAIL",
        "objects": len(object_ids),
        "provenance_mappings": len(provenance.get("mappings", [])),
        "relations": len(relations.get("relations", [])),
        "negative_hold_classes": len(neg_ids),
        "skills": len(skill_ids),
        "theorem_dependencies": len(dep_theorems),
        "objectization_fingerprint": hashlib.sha256(payload).hexdigest(),
        "authority_delta": "NONE",
        "errors": errors,
        "does_not_establish": [
            "formal theoremhood",
            "empirical confirmation",
            "scientific validity",
            "release eligibility",
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
