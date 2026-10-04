#!/usr/bin/env python3
"""Deterministic bootstrap validator for CodexStation Ω Public."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md","AGENTS.md","MANIFEST.json",
    "canon/OMEGA_CORE.md","canon/OMEGA_CRYSTAL.md",
    "canon/OMEGA_SKILL_SPINDLE.md","canon/OMEGA_THEOREMATIC_SPINE.md",
    "canon/OMEGA_PUBLIC_ANCHORS.md",
]
CANARIES = [
    "PUBLICATION != AUTHORITY_PROMOTION",
    "PLATFORM_PROFILE != CANON_FORK",
    "MODEL != REALITY",
    "SOURCE != AUTHORITY",
    "CLAIM != EVIDENCE",
    "FORMAL_PROOF != EMPIRICAL_CONFIRMATION",
    "IMPLEMENTATION_PASS != SCIENTIFIC_PASS",
    "SAME_LABEL != SAME_LINEAGE",
]
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
]

def text_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and ".git" not in p.parts and p.suffix.lower() in {".md",".json",".py",".yml",".yaml",".txt"}:
            yield p

def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fail(msg: str, errors: list[str]):
    errors.append(msg)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["bootstrap","release"],default="bootstrap")
    args=ap.parse_args()
    errors=[]
    for rel in REQUIRED:
        if not (ROOT/rel).is_file():
            fail(f"missing required file: {rel}",errors)

    manifest_path=ROOT/"MANIFEST.json"
    if manifest_path.is_file():
        try:
            manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            fail(f"MANIFEST.json parse failure: {e}",errors)
            manifest={}
        if manifest.get("authority_delta") != "NONE":
            fail("bootstrap authority_delta must be NONE",errors)
        gates=manifest.get("publication_gates",{})
        if any(v=="FAIL" for v in gates.values()):
            fail("publication gate is FAIL",errors)
        if args.mode=="release":
            for k,v in gates.items():
                if v!="PASS":
                    fail(f"release gate not PASS: {k}={v}",errors)
            if not manifest.get("release_eligible",False):
                fail("release_eligible is false",errors)

    corpus="\n".join((ROOT/r).read_text(encoding="utf-8",errors="replace") for r in REQUIRED if (ROOT/r).is_file())
    for c in CANARIES:
        if c not in corpus:
            fail(f"constitutional canary missing: {c}",errors)

    for p in text_files():
        t=p.read_text(encoding="utf-8",errors="replace")
        for pat in SECRET_PATTERNS:
            if pat.search(t):
                fail(f"secret-like pattern in {p.relative_to(ROOT)}",errors)

    files={str(p.relative_to(ROOT)):sha256(p) for p in sorted(text_files())}
    fingerprint=hashlib.sha256(
        "\n".join(f"{k}:{v}" for k,v in sorted(files.items())).encode()
    ).hexdigest()
    report={
        "mode":args.mode,
        "result":"PASS" if not errors else "FAIL",
        "authority_delta":"NONE",
        "semantic_fingerprint":fingerprint,
        "checked_file_count":len(files),
        "errors":errors,
        "does_not_establish":[
            "scientific validity",
            "formal theoremhood",
            "empirical confirmation",
            "general intelligence",
            "release eligibility unless release mode passes"
        ]
    }
    print(json.dumps(report,indent=2))
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
