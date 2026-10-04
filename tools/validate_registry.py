#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "OMEGA_REGISTRY.json"

def unique_ids(items, label, errors):
    seen = set()
    for item in items:
        item_id = item.get("id")
        if not item_id:
            errors.append(f"{label}: missing id")
        elif item_id in seen:
            errors.append(f"{label}: duplicate id {item_id}")
        seen.add(item_id)
    return seen

def main():
    errors = []
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    if data.get("authority_delta") != "NONE":
        errors.append("registry authority_delta must remain NONE during staging")

    object_ids = unique_ids(data.get("objects", []), "objects", errors)
    unique_ids(data.get("relations", []), "relations", errors)
    unique_ids(data.get("theorematic_objects", []), "theorematic_objects", errors)
    unique_ids(data.get("skills", []), "skills", errors)
    unique_ids(data.get("anchors", []), "anchors", errors)
    unique_ids(data.get("gates", []), "gates", errors)

    allowed_relations = set(data.get("relation_types", []))
    for rel in data.get("relations", []):
        if rel.get("type") not in allowed_relations:
            errors.append(f"unknown relation type: {rel.get('type')}")
        if rel.get("from") not in object_ids:
            errors.append(f"missing relation source: {rel.get('id')}")
        if rel.get("to") not in object_ids:
            errors.append(f"missing relation target: {rel.get('id')}")

    for rule in data.get("noncollapse", []):
        if rule.get("lhs") not in object_ids or rule.get("rhs") not in object_ids:
            errors.append(f"noncollapse endpoint missing: {rule}")

    required_axes = {"formal", "empirical", "execution", "reproduction", "implementation", "publication", "canon"}
    if set(data.get("status_model", {})) != required_axes:
        errors.append("status vector axes mismatch")

    for theorem in data.get("theorematic_objects", []):
        if theorem.get("class") == "THEOREM_TARGET" and theorem.get("proof_status") in {"MACHINE_CHECKED", "INDEPENDENT_CHECKED"}:
            errors.append(f"theorem target silently promoted: {theorem.get('id')}")

    for skill in data.get("skills", []):
        if not skill.get("guards"):
            errors.append(f"skill missing guards: {skill.get('id')}")
        if not skill.get("source_refs"):
            errors.append(f"skill missing source refs: {skill.get('id')}")

    for gate in data.get("gates", []):
        if gate.get("authority_delta") != "NONE":
            errors.append(f"gate authority delta is not NONE: {gate.get('id')}")

    raw = REGISTRY.read_bytes()
    report = {
        "result": "PASS" if not errors else "FAIL",
        "registry_sha256": hashlib.sha256(raw).hexdigest(),
        "objects": len(data.get("objects", [])),
        "relations": len(data.get("relations", [])),
        "noncollapse_rules": len(data.get("noncollapse", [])),
        "theorematic_objects": len(data.get("theorematic_objects", [])),
        "skills": len(data.get("skills", [])),
        "anchors": len(data.get("anchors", [])),
        "gates": len(data.get("gates", [])),
        "authority_delta": "NONE",
        "errors": errors,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
