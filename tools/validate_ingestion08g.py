#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from ingestion08g.ingest import classify,ingest

PREVIOUS="ac43b3f0ccd001bc4235f1e19331e03819d5694393dbc7733cb0bfb56065428c"
FILES=[
 "ingestion08g/INGESTION_POLICY.json",
 "ingestion08g/RECEIPT_REGISTRY.json",
 "ingestion08g/ingest.py",
 "tools/validate_ingestion08g.py",
 "publication/SLICE_08G_RECEIPT.json"
]

def synthetic(family,status="PASS",evidence_class="DIRECT_RUNNER_EXECUTION"):
    pins=json.loads((ROOT/"bridge08f/EXPECTED_PINS.json").read_text())
    pin={x["source_family"]:x for x in pins["sources"]}[family]
    return {
      "schema":"GILC/CODEXSTATION/OMEGA-PRIVATE-REPRODUCTION-RECEIPT/0.8f",
      "source_family":family,"repository":pin["repository"],"source_commit":pin["source_commit"],
      "runner_identity":{"provider":"08G_VALIDATOR","run_id":"SYNTHETIC_VECTOR","runner_commit":"validator"},
      "commands":pin["native_commands"],
      "results":[{"command":x,"status":status} for x in pin["native_commands"]],
      "overall_status":status if status in ("PASS","FAIL") else "HOLD",
      "scope":pin["expected_receipt_scope"],"sanitized":True,"private_source_disclosed":False,
      "source_tree_modified_for_test":False,"authority_delta":"NONE","evidence_class":evidence_class
    }

def fingerprint():
    h=hashlib.sha256()
    for rel in FILES:
        raw=(ROOT/rel).read_bytes(); h.update(rel.encode()); h.update(b"\0"); h.update(raw); h.update(b"\0")
    s=h.hexdigest(); return s,hashlib.sha256((PREVIOUS+"|"+s).encode()).hexdigest()

def main():
    errors=[]
    policy=json.loads((ROOT/"ingestion08g/INGESTION_POLICY.json").read_text())
    registry=json.loads((ROOT/"ingestion08g/RECEIPT_REGISTRY.json").read_text())
    receipt=json.loads((ROOT/"publication/SLICE_08G_RECEIPT.json").read_text())
    if policy.get("predecessor_composite_semantic_fingerprint")!=PREVIOUS:
        errors.append("predecessor mismatch")
    if set(x["verdict"] for x in registry["families"].values())!={"HOLD_NO_RECEIPT"}:
        errors.append("initial registry must remain HOLD_NO_RECEIPT")
    if classify(synthetic("NEURAL_LATTICE",evidence_class="SYNTHETIC_SCHEMA_TEST"))["verdict"]!="REJECT_NON_EXECUTION_EVIDENCE":
        errors.append("synthetic promotion guard failed")
    direct=synthetic("NEURAL_LATTICE")
    if classify(direct)["verdict"]!="PASS_REPRODUCED":
        errors.append("direct pass classification failed")
    failed=synthetic("NEURAL_LATTICE","FAIL")
    if classify(failed)["verdict"]!="FAIL_REPRODUCTION":
        errors.append("failure classification failed")
    r2,d=ingest(registry,direct)
    if d["verdict"]!="PASS_REPRODUCED" or r2["families"]["DIGITAL_FABRICA_CORE"]["verdict"]!="HOLD_NO_RECEIPT":
        errors.append("family-isolated promotion failed")
    conflict=synthetic("NEURAL_LATTICE"); conflict["runner_identity"]["run_id"]="DIFFERENT"
    _,cd=ingest(r2,conflict)
    if cd["verdict"]!="REJECT_CONFLICT":
        errors.append("conflict guard failed")
    if receipt.get("status")!="INGESTION_CAPABILITY_PASS_NO_NEW_RECEIPTS":
        errors.append("slice status mismatch")
    if policy.get("authority_delta")!="NONE" or registry.get("authority_delta")!="NONE" or receipt.get("authority_delta")!="NONE":
        errors.append("authority delta must remain NONE")
    sf,cf=fingerprint()
    print(json.dumps({"result":"PASS" if not errors else "FAIL","slice":"OMEGA_TIER_A_PRIVATE_RECEIPT_INGESTION_SLICE_08G","registry_state":{k:v["verdict"] for k,v in registry["families"].items()},"slice_fingerprint":sf,"composite_semantic_fingerprint":cf,"authority_delta":"NONE","release_eligible":False,"errors":errors},indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    raise SystemExit(main())
