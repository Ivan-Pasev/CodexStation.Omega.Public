#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREVIOUS = "cf9bc1de879c91756640cc145538324787646868811fa8ca9007e363b11c7de3"
FILES = [
    "runtime08c/runtime.py",
    "runtime08c/adapters.py",
    "runtime08c/__init__.py",
    "runtime08c/RUNTIME_PROFILE.json",
    "runtime08c/REFERENCE_SCENARIOS.json",
    "aggregation08c/SEMANTIC_EXTENSION.json",
    "aggregation08c/RUNTIME_CONTRACT.md",
]


def fingerprint() -> tuple[str, str]:
    h = hashlib.sha256()
    for rel in FILES:
        raw = (ROOT / rel).read_bytes()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(raw)
        h.update(b"\0")
    slice_fp = h.hexdigest()
    composite = hashlib.sha256((PREVIOUS + "|" + slice_fp).encode()).hexdigest()
    return slice_fp, composite


def main() -> int:
    errors = []
    profile = json.loads((ROOT / "runtime08c/RUNTIME_PROFILE.json").read_text())
    extension = json.loads((ROOT / "aggregation08c/SEMANTIC_EXTENSION.json").read_text())
    scenarios = json.loads((ROOT / "runtime08c/REFERENCE_SCENARIOS.json").read_text())

    if profile.get("previous_composite_semantic_fingerprint") != PREVIOUS:
        errors.append("profile previous composite mismatch")
    if extension.get("previous_composite_semantic_fingerprint") != PREVIOUS:
        errors.append("extension previous composite mismatch")
    if profile.get("authority_delta") != "NONE" or extension.get("authority_delta") != "NONE":
        errors.append("authority_delta must remain NONE")
    if profile.get("release_eligible") is not False or extension.get("release_eligible") is not False:
        errors.append("release eligibility must remain false")
    if profile.get("external_effect_default") != "UNKNOWN_OUTCOME_AND_HOLD":
        errors.append("external effect default must preserve unknown outcome")
    if len(profile.get("source_adapters", [])) != 5:
        errors.append("expected five Tier-A adapters")
    if len(scenarios.get("scenarios", [])) < 6:
        errors.append("insufficient reference scenarios")

    required_laws = {
        "NO_SUCCESSOR_AUTHORITY_BOOTSTRAP",
        "PARENT_STATE_IDENTITY_MUST_MATCH_CURRENT_STATE",
        "PROTECTED_INVARIANTS_FAIL_CLOSED",
        "EXACT_AUTHORIZED_PLAN_BINDING_REQUIRED",
        "UNKNOWN_OUTCOME_IS_PRESERVED_AS_UNKNOWN",
        "CONFLICT_IS_DURABLE_STATE",
    }
    if not required_laws.issubset(set(profile.get("invariants", []))):
        errors.append("required constitutional laws missing")

    # Fast executable smoke check independent of unittest discovery.
    code = r'''
from runtime08c.runtime import make_state, compile_archetonic_plate, execute_transition, recovery_check
s=make_state(project_id="p",grants=[{"grant_id":"g","principal_id":"a","level":"A2","rights":[],"scope":["*"]}])
t=compile_archetonic_plate(plate_id="p1",project_id="p",state=s,principal_id="a",operations=[{"op":"SET","key":"x","value":1}],required_authority=["A2"],protected_invariants=["i"])
r=execute_transition(s,t,semantic_decision={"status":"ALLOW"},invariant_results=[{"invariant_id":"i","status":"PASS","evidence_refs":[]}])
assert r["status"]=="PASS"
assert recovery_check(s,r["state"],r["receipt"])["status"]=="RECOVERABLE"
'''
    p = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        errors.append("runtime smoke failed: " + (p.stdout + p.stderr)[-800:])

    slice_fp, composite = fingerprint()
    report = {
        "result": "PASS" if not errors else "FAIL",
        "runtime_id": profile["runtime_id"],
        "source_adapters": len(profile["source_adapters"]),
        "reference_scenarios": len(scenarios["scenarios"]),
        "slice_fingerprint": slice_fp,
        "composite_semantic_fingerprint": composite,
        "authority_delta": "NONE",
        "errors": errors,
        "does_not_establish": [
            "production readiness",
            "external effect confirmation",
            "full cross-repository integration",
            "formal theoremhood",
            "live provider conformance",
            "release eligibility",
        ],
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
