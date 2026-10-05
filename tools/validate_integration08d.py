#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from integration08d.harness import run_all

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = "f2a0eba01d21d652720b46a74664da5d5b6f5cd0fcc7c6170da7ab8f4b38ab64"
FILES = [
    "integration08d/SOURCE_FIXTURES.json",
    "integration08d/HARNESS_PROFILE.json",
    "integration08d/harness.py",
    "aggregation08d/INTEGRATION_CONTRACT.md",
    "aggregation08d/SEMANTIC_EXTENSION.json",
    "tests/test_integration08d.py",
]


def fingerprint():
    h = hashlib.sha256()
    for rel in FILES:
        raw = (ROOT/rel).read_bytes()
        h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    slice_fp = h.hexdigest()
    composite = hashlib.sha256((PREVIOUS + "|" + slice_fp).encode()).hexdigest()
    return slice_fp, composite


def main():
    errors = []
    profile = json.loads((ROOT/"integration08d/HARNESS_PROFILE.json").read_text())
    fixtures_doc = json.loads((ROOT/"integration08d/SOURCE_FIXTURES.json").read_text())
    bindings = json.loads((ROOT/"aggregation08b/SOURCE_BINDINGS.json").read_text())
    extension = json.loads((ROOT/"aggregation08d/SEMANTIC_EXTENSION.json").read_text())

    if profile.get("authority_delta") != "NONE" or extension.get("authority_delta") != "NONE":
        errors.append("authority_delta must remain NONE")
    if profile.get("release_eligible") is not False or extension.get("release_eligible") is not False:
        errors.append("release_eligible must remain false")
    if fixtures_doc.get("previous_composite_semantic_fingerprint") != PREVIOUS:
        errors.append("fixture predecessor fingerprint mismatch")
    if extension.get("previous_composite_semantic_fingerprint") != PREVIOUS:
        errors.append("extension predecessor fingerprint mismatch")

    bound = {b["repository"]: b["commit"] for b in bindings["bindings"]}
    fixtures = fixtures_doc.get("fixtures", [])
    if len(fixtures) != 5:
        errors.append("expected exactly five Tier-A source fixtures")
    for fixture in fixtures:
        if bound.get(fixture["repository"]) != fixture["commit"]:
            errors.append("fixture commit mismatch: " + fixture["repository"])
        if not fixture.get("residuals"):
            errors.append("fixture must expose residuals: " + fixture["fixture_id"])

    report = run_all()
    if report["result"] != "PASS":
        errors.append("integration harness failed")
    if report["source_families"] != 5:
        errors.append("harness did not execute five source families")

    required = {
        "SOURCE_FIXTURE != SOURCE_RUNTIME_EXECUTION",
        "NORMALIZATION != SEMANTIC_IDENTITY",
        "ADAPTER_PASS != FULL_SOURCE_INTEGRATION",
        "SOURCE_REPORTED_PASS != LOCALLY_REPRODUCED_PASS",
    }
    if not required.issubset(set(fixtures_doc.get("laws", []))):
        errors.append("required non-collapse laws missing")

    slice_fp, composite = fingerprint()
    out = {
        "result":"PASS" if not errors else "FAIL",
        "harness_id":profile["harness_id"],
        "source_families":report["source_families"],
        "fixture_results":{x["source_family"]:x["status"] for x in report["results"]},
        "slice_fingerprint":slice_fp,
        "composite_semantic_fingerprint":composite,
        "authority_delta":"NONE",
        "release_eligible":False,
        "errors":errors,
        "does_not_establish":[
            "source repository execution",
            "production integration",
            "external effect confirmation",
            "independent reproduction",
            "formal theoremhood",
            "scientific confirmation",
            "live provider conformance",
            "release eligibility",
        ],
    }
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
