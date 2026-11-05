"""Slice 07 synthetic evidence package tests: never execute host probes."""
import copy
import json
import unittest
from pathlib import Path
from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_host_qualification import compile_host_pilot_plan
from runtime08c.uhp_witness import snapshot_manifest
from runtime08c.uhp_capture_intake import evaluate_capture_intake

MATRIX = Path(__file__).resolve().parents[1] / "ops/uhp06/qualification_matrix.json"


def fixture():
    matrix = json.loads(MATRIX.read_text())
    source = {"README.md": b"# synthetic only\n", "a.py": b"print('ok')\n"}
    cfg = {
        "project_id": "p07", "work_order_id": "w07",
        "source_commit": "a" * 40,
        "source_digest": snapshot_manifest(source)["digest"],
        "observer_host_id": "observer:synthetic",
        "executor_host_id": "executor:synthetic",
        "observer_principal_id": "observer:principal",
        "executor_principal_id": "executor:principal",
        "execution_scope": "DISPOSABLE_READ_ONLY_NO_PROVIDER",
    }
    plan = compile_host_pilot_plan(cfg, matrix)
    refs = ["evidence_%s.json" % p["id"] for p in plan["negative_probes"]]
    report = {
        "schema": "codexstation.omega.uhp.host-pilot-report.v0.1",
        "plan_digest": plan["plan_digest"],
        **{k: cfg[k] for k in (
            "project_id", "work_order_id", "source_commit", "source_digest",
            "observer_host_id", "executor_host_id",
            "observer_principal_id", "executor_principal_id")},
        "probes": [
            {"id":p["id"], "observed":p["expected"],
             "evidence_ref": ref}
            for p,ref in zip(plan["negative_probes"], refs)
        ],
    }
    blobs={}
    for i,(p,ref) in enumerate(zip(plan["negative_probes"],refs),1):
        event = {
            "schema": "codexstation.omega.uhp.probe-event.v0.1",
            "plan_digest": plan["plan_digest"],
            "probe_id": p["id"], "observed": p["expected"],
            "observer_host_id": cfg["observer_host_id"],
            "executor_host_id": cfg["executor_host_id"],
            "observer_principal_id": cfg["observer_principal_id"],
            "executor_principal_id": cfg["executor_principal_id"],
            "collector_session": "session:synthetic",
            "sequence": i, "capture_epoch": 1793890000 + i,
            "nonce": "nonce:%02d" % i,
        }
        blobs[ref] = json.dumps(event,sort_keys=True).encode()
    capture = {
        "schema": "codexstation.omega.uhp.capture-claim.v0.1",
        "plan_digest": plan["plan_digest"],
        "observer_host_id": cfg["observer_host_id"],
        "executor_host_id": cfg["executor_host_id"],
        "observer_principal_id": cfg["observer_principal_id"],
        "executor_principal_id": cfg["executor_principal_id"],
        "collector_session": "session:synthetic",
        "event_refs": refs,
        "source_before_digest": snapshot_manifest(source)["digest"],
        "source_after_digest": snapshot_manifest(source)["digest"],
    }
    return plan,matrix,report,capture,blobs,source,copy.deepcopy(source)


def check(values=None):
    return evaluate_capture_intake(*(fixture() if values is None else values))


class CaptureIntakeTests(unittest.TestCase):
    def test_complete_claim_remains_unattested(self):
        v=check()
        self.assertEqual(v["verdict"], "CAPTURE_BYTES_CONSISTENT_INDEPENDENCE_HOLD")
        self.assertEqual(v["probe_event_count"],12)
        self.assertTrue(v["supplied_bytes_hashed"])
        for k in ("capture_provenance_independently_verified",
                  "observer_host_independently_verified", "observer_key_custody_verified",
                  "technical_sandbox_enforcement_verified","trusted_timestamp_verified",
                  "durable_replay_committed","independent_effects_verified",
                  "actual_host_run_performed_by_this_api",
                  "dispatch_authorized","promotion_authorized"):
            self.assertFalse(v[k],k)
        self.assertEqual(v["canonical_authority_delta"],"NONE")

    def test_deterministic(self):
        self.assertEqual(check(),check())

    def test_no_raw_event_leaked(self):
        v=check()
        self.assertNotIn("nonce:01",str(v))
        self.assertNotIn("print('ok')",str(v))

    def test_missing_artifact_is_error(self):
        x=list(fixture())
        del x[4][x[3]["event_refs"][0]]
        with self.assertRaises(UHPContractError): check(x)

    def test_extra_artifact_is_error(self):
        x=list(fixture())
        x[4]["extra.json"]=b"{}"
        with self.assertRaises(UHPContractError): check(x)

    def test_source_was_mutated_holds(self):
        x=list(fixture())
        x[6]["a.py"]=b"evil"
        x[3]["source_after_digest"]=snapshot_manifest(x[6])["digest"]
        self.assertIn("SOURCE_MUTATED_IN_SUPPLIED_SNAPSHOTS",check(x)["reasons"])

    def test_source_pin_changed_holds(self):
        x=list(fixture())
        x[5]["README.md"]=b"other"
        x[3]["source_before_digest"]=snapshot_manifest(x[5])["digest"]
        self.assertIn("SOURCE_PRE_CAPTURE_DIFFERS_FROM_PIN",check(x)["reasons"])

    def test_unbound_source_digest_errors(self):
        x=list(fixture())
        x[3]["source_after_digest"]="sha256:"+"f"*64
        with self.assertRaises(UHPContractError): check(x)

    def test_wrong_observer_claim_errors(self):
        x=list(fixture())
        x[3]["observer_host_id"]="host:other"
        with self.assertRaises(UHPContractError): check(x)

    def test_wrong_plan_digest_errors(self):
        x=list(fixture())
        x[3]["plan_digest"]="sha256:"+"f"*64
        with self.assertRaises(UHPContractError): check(x)

    def test_wrong_event_plan_holds(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["plan_digest"]="sha256:"+"f"*64
        x[4][ref]=json.dumps(evt).encode()
        self.assertIn("EVENT_PLAN_BINDING_MISMATCH",check(x)["reasons"])

    def test_wrong_event_host_holds(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["observer_host_id"]="foreign:host"
        x[4][ref]=json.dumps(evt).encode()
        self.assertIn("EVENT_OBSERVER_EXECUTOR_BINDING_MISMATCH",check(x)["reasons"])

    def test_failed_denial_holds(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["observed"]="ALLOWED"
        x[4][ref]=json.dumps(evt).encode()
        x[2]["probes"][0]["observed"]="ALLOWED"
        self.assertIn("NEGATIVE_PROBE_FAILED_IN_CAPTURE",check(x)["reasons"])

    def test_divergence_report_and_event_holds(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["observed"]="ALLOWED"
        x[4][ref]=json.dumps(evt).encode()
        self.assertIn("REPORT_EVENT_OUTCOME_MISMATCH",check(x)["reasons"])

    def test_report_mismatched_ref_holds(self):
        x=list(fixture())
        x[2]["probes"][0]["evidence_ref"]="evidence_other.json"
        self.assertIn("REPORT_EVIDENCE_REFERENCE_MISMATCH",check(x)["reasons"])

    def test_tampered_probe_id_errors(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["probe_id"]="N999"
        x[4][ref]=json.dumps(evt).encode()
        with self.assertRaises(UHPContractError): check(x)

    def test_repeated_probe_id_errors(self):
        x=list(fixture())
        ref=x[3]["event_refs"][1]
        evt=json.loads(x[4][ref])
        evt["probe_id"]="N01"
        x[4][ref]=json.dumps(evt).encode()
        with self.assertRaises(UHPContractError): check(x)

    def test_mismatched_sequence_holds(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["sequence"]=6
        x[4][ref]=json.dumps(evt).encode()
        self.assertIn("EVENT_SEQUENCE_GAP",check(x)["reasons"])

    def test_replayed_nonce_holds(self):
        x=list(fixture())
        ref=x[3]["event_refs"][1]
        evt=json.loads(x[4][ref])
        evt["nonce"]="nonce:01"
        x[4][ref]=json.dumps(evt).encode()
        self.assertIn("EVENT_NONCE_DUPLICATE_IN_CAPTURE",check(x)["reasons"])

    def test_backwards_clock_holds(self):
        x=list(fixture())
        ref=x[3]["event_refs"][1]
        evt=json.loads(x[4][ref])
        evt["capture_epoch"]=1
        x[4][ref]=json.dumps(evt).encode()
        self.assertIn("EVENT_TIMESTAMP_OUT_OF_ORDER",check(x)["reasons"])

    def test_malformed_json_errors(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        x[4][ref]=b"this is not JSON"
        with self.assertRaises(UHPContractError): check(x)

    def test_duplicate_json_key_errors(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        value=x[4][ref].decode()
        x[4][ref]=value.replace('{"capture_epoch":','{"capture_epoch":0,"capture_epoch":').encode()
        with self.assertRaises(UHPContractError): check(x)

    def test_oversize_event_errors(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        x[4][ref]=b" " * 4097
        with self.assertRaises(UHPContractError): check(x)

    def test_event_control_character_rejected(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["nonce"]="bad\nnonce"
        x[4][ref]=json.dumps(evt).encode()
        with self.assertRaises(UHPContractError): check(x)

    def test_nonfinite_or_nan_rejected(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        s=x[4][ref].decode()
        x[4][ref]=s.replace('"sequence": 1','"sequence": NaN').encode()
        with self.assertRaises(UHPContractError): check(x)

    def test_unsupported_extra_event_field_rejected(self):
        x=list(fixture())
        ref=x[3]["event_refs"][0]
        evt=json.loads(x[4][ref])
        evt["authorize"]=True
        x[4][ref]=json.dumps(evt).encode()
        with self.assertRaises(UHPContractError): check(x)

    def test_duplicate_capture_refs_errors(self):
        x=list(fixture())
        x[3]["event_refs"][1]=x[3]["event_refs"][0]
        with self.assertRaises(UHPContractError): check(x)

    def test_invalid_capture_ref_path_errors(self):
        x=list(fixture())
        x[3]["event_refs"][0]="../secret.json"
        with self.assertRaises(UHPContractError): check(x)

    def test_input_immutability(self):
        x=fixture()
        earlier=copy.deepcopy(x)
        check(x)
        self.assertEqual(x,earlier)


if __name__=="__main__":
    unittest.main()
