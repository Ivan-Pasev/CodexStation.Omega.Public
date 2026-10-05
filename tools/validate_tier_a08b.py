#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, pathlib, re

ROOT=pathlib.Path(__file__).resolve().parents[1]
PREVIOUS="d0c0881da6c03dc797fea53a0c4c22caf9913c7de4c52ff018265fca9dbd3d4c"
FILES=[
  "aggregation08b/SOURCE_BINDINGS.json",
  "aggregation08b/CONSTITUTIONAL_ABI.json",
  "aggregation08b/ADAPTER_MAP.json",
  "aggregation08b/KERNEL_BINDINGS.json",
  "aggregation08b/ABI_TEST_VECTORS.json",
  "aggregation08b/SEMANTIC_EXTENSION.json",
]
HEX40=re.compile(r"^[0-9a-f]{40}$")

def load(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8"))
def canon(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def fingerprints():
    h=hashlib.sha256()
    for rel in FILES:
        h.update(canon(load(rel))); h.update(b"\n")
    s=h.hexdigest()
    return s, hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    src,abi,adp,kb,vec,ext=[load(x) for x in FILES]
    binds=src["bindings"]
    if len(binds)!=5: errors.append("expected five Tier-A bindings")
    ids={b["binding_id"] for b in binds}
    if len(ids)!=5: errors.append("duplicate source binding ids")
    for b in binds:
        if not HEX40.match(b.get("commit","")): errors.append("invalid commit pin: "+b.get("binding_id","?"))
        if not b.get("paths"): errors.append("missing pinned paths: "+b.get("binding_id","?"))
        for p in b.get("paths",[]):
            if not HEX40.match(p.get("blob","")): errors.append("invalid blob pin: "+p.get("path","?"))
    required={"CanonicalDigest","Principal","AuthorityGrant","CanonicalState","CandidateTransition","InvariantEvaluation","DecisionVector","Event","Receipt","Conflict","RecoveryEvidence"}
    if set(abi.get("primitives",{}))!=required: errors.append("ABI primitive set mismatch")
    if abi.get("authority_delta")!="NONE": errors.append("ABI authority delta")
    adapters=adp.get("adapters",[])
    if {a["source_binding"] for a in adapters}!=ids: errors.append("adapter coverage mismatch")
    for a in adapters:
        if not a.get("mappings"): errors.append("adapter without mappings: "+a["adapter_id"])
        if "open_gaps" not in a: errors.append("adapter missing open_gaps: "+a["adapter_id"])
    if {x["source_binding"] for x in kb.get("bindings",[])}!=ids: errors.append("kernel binding coverage mismatch")
    if len(vec.get("vectors",[]))<4: errors.append("insufficient ABI vectors")
    if ext.get("previous_composite_semantic_fingerprint")!=PREVIOUS: errors.append("previous composite mismatch")
    for g in ["NB00_LIVE_CONFORMANCE_01","RGT-04_BUNDLED_FALLBACK_CLEAN_CHAT","LICENSE_IP_REVIEW"]:
        if g not in ext.get("parallel_open_gates",[]): errors.append("missing open gate "+g)
    if ext.get("release_eligible") is not False: errors.append("release must remain false")
    s,c=fingerprints()
    print(json.dumps({
      "result":"PASS" if not errors else "FAIL",
      "source_bindings":len(binds),
      "pinned_paths":sum(len(b["paths"]) for b in binds),
      "abi_primitives":len(required),
      "adapters":len(adapters),
      "kernel_bindings":len(kb.get("bindings",[])),
      "vectors":len(vec.get("vectors",[])),
      "slice_fingerprint":s,
      "composite_semantic_fingerprint":c,
      "authority_delta":"NONE",
      "errors":errors,
      "does_not_establish":["cross-repo integration pass","live host conformance","production readiness","independent reproduction","release eligibility"]
    },indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
