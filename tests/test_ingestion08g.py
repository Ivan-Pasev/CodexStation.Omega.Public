import json
import unittest
from pathlib import Path

from ingestion08g.ingest import classify, ingest

ROOT=Path(__file__).resolve().parents[1]
PINS={x["source_family"]:x for x in json.loads((ROOT/"bridge08f/EXPECTED_PINS.json").read_text())["sources"]}
REGISTRY=json.loads((ROOT/"ingestion08g/RECEIPT_REGISTRY.json").read_text())

def receipt(family,status="PASS",evidence_class="DIRECT_RUNNER_EXECUTION"):
    pin=PINS[family]
    return {
        "schema":"GILC/CODEXSTATION/OMEGA-PRIVATE-REPRODUCTION-RECEIPT/0.8f",
        "source_family":family,
        "repository":pin["repository"],
        "source_commit":pin["source_commit"],
        "runner_identity":{"provider":"TEST","run_id":"R1","runner_commit":"runner"},
        "commands":pin["native_commands"],
        "results":[{"command":c,"status":status} for c in pin["native_commands"]],
        "overall_status":status if status in ("PASS","FAIL") else "HOLD",
        "scope":pin["expected_receipt_scope"],
        "sanitized":True,
        "private_source_disclosed":False,
        "source_tree_modified_for_test":False,
        "authority_delta":"NONE",
        "evidence_class":evidence_class
    }

class Ingestion08GTests(unittest.TestCase):
    def test_initial_registry_is_hold_only(self):
        self.assertEqual({v["verdict"] for v in REGISTRY["families"].values()},{"HOLD_NO_RECEIPT"})

    def test_direct_pass_promotes_one_family_only(self):
        out,decision=ingest(REGISTRY,receipt("NEURAL_LATTICE"))
        self.assertEqual(decision["verdict"],"PASS_REPRODUCED")
        self.assertEqual(out["families"]["NEURAL_LATTICE"]["verdict"],"PASS_REPRODUCED")
        self.assertEqual(out["families"]["HIGHESTONE"]["verdict"],"HOLD_NO_RECEIPT")

    def test_failure_is_evidence_not_rejection(self):
        self.assertEqual(classify(receipt("NEURAL_LATTICE","FAIL"))["verdict"],"FAIL_REPRODUCTION")

    def test_incomplete_is_hold(self):
        self.assertEqual(classify(receipt("NEURAL_LATTICE","SKIP"))["verdict"],"HOLD_INCOMPLETE")

    def test_synthetic_cannot_promote(self):
        self.assertEqual(classify(receipt("NEURAL_LATTICE",evidence_class="SYNTHETIC_SCHEMA_TEST"))["verdict"],"REJECT_NON_EXECUTION_EVIDENCE")

    def test_wrong_pin_is_rejected(self):
        r=receipt("HIGHESTONE"); r["source_commit"]="0"*40
        self.assertEqual(classify(r)["verdict"],"REJECT_INVALID_RECEIPT")

    def test_conflicting_second_receipt_is_rejected(self):
        first=receipt("NEURAL_LATTICE")
        state,_=ingest(REGISTRY,first)
        second=receipt("NEURAL_LATTICE")
        second["runner_identity"]["run_id"]="R2"
        _,decision=ingest(state,second)
        self.assertEqual(decision["verdict"],"REJECT_CONFLICT")

if __name__=="__main__":
    unittest.main()
