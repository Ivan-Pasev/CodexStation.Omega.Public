"""Pure qualification-contract tests. No host, container or model is started."""
import copy
import json
import unittest
from pathlib import Path

from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_host_qualification import compile_host_pilot_plan, assess_report

MATRIX_PATH = Path(__file__).resolve().parents[1] / "ops/uhp06/qualification_matrix.json"


def matrix():
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def config():
    return {
        "project_id": "p06", "work_order_id": "w06",
        "source_commit": "a" * 40,
        "source_digest": "sha256:" + "b" * 64,
        "observer_host_id": "host:observer",
        "executor_host_id": "host:executor",
        "observer_principal_id": "principal:observer",
        "executor_principal_id": "principal:executor",
        "execution_scope": "DISPOSABLE_READ_ONLY_NO_PROVIDER",
    }


def plan():
    return compile_host_pilot_plan(config(), matrix())


def report():
    p = plan()
    c = p["config"]
    return {
        "schema": "codexstation.omega.uhp.host-pilot-report.v0.1",
        "plan_digest": p["plan_digest"],
        **{k:c[k] for k in ("project_id", "work_order_id",
            "source_commit", "source_digest", "observer_host_id",
            "executor_host_id", "observer_principal_id",
            "executor_principal_id")},
        "probes": [
            {"id":p0["id"], "observed":p0["expected"],
             "evidence_ref": "evidence:" + p0["id"]}
            for p0 in p["negative_probes"]
        ],
    }


class UHPHostQualificationTests(unittest.TestCase):
    def test_plan_is_non_executable(self):
        p = plan()
        self.assertFalse(p["operator_execute_approved"])
        self.assertFalse(p["live_run_performed"])
        self.assertFalse(p["dispatch_authorized"])
        self.assertFalse(p["promotion_authorized"])
        self.assertFalse(p["host_identity_verified"])
        self.assertFalse(p["independent_observer_verified"])
        self.assertEqual(p["canonical_authority_delta"], "NONE")

    def test_static_claims_are_never_independent_proof(self):
        r = assess_report(plan(), matrix(), report())
        self.assertEqual(r["verdict"], "CLAIMS_COMPLETE_INDEPENDENT_PROOF_REQUIRED")
        self.assertFalse(r["independent_capture_verified"])
        self.assertFalse(r["independent_host_identity_verified"])
        self.assertFalse(r["technical_isolation_verified"])
        self.assertFalse(r["external_effects_verified"])
        self.assertFalse(r["dispatch_authorized"])

    def test_plan_deterministic(self):
        self.assertEqual(plan(), plan())

    def test_matrix_not_empty_or_duplicate(self):
        m = matrix()
        self.assertGreaterEqual(len(m["negative_probes"]), 8)
        self.assertEqual(len({p["id"] for p in m["negative_probes"]}),
                         len(m["negative_probes"]))

    def test_same_host_not_separate(self):
        c = config()
        c["observer_host_id"] = c["executor_host_id"]
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(c, matrix())

    def test_same_principal_not_separate(self):
        c = config()
        c["observer_principal_id"] = c["executor_principal_id"]
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(c, matrix())

    def test_bad_source_pin(self):
        c = config()
        c["source_commit"] = "branch-main"
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(c, matrix())

    def test_bad_source_hash(self):
        c = config()
        c["source_digest"] = "sha256:" + "Q"*64
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(c, matrix())

    def test_more_privileged_scope_rejected(self):
        c = config()
        c["execution_scope"] = "LIVE_WITH_PROVIDER"
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(c, matrix())

    def test_matrix_dispatch_intent_rejected(self):
        m = matrix()
        m["intent"] = "RUN_NOW"
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(config(), m)

    def test_matrix_missing_required_categories_rejected(self):
        m = matrix()
        m["negative_probes"] = [p for p in m["negative_probes"] if p["expected"] != "NO_AUTO_RETRY"]
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(config(), m)

    def test_matrix_duplicate_probe_rejected(self):
        m = matrix()
        m["negative_probes"].append(copy.deepcopy(m["negative_probes"][0]))
        with self.assertRaises(UHPContractError):
            compile_host_pilot_plan(config(), m)

    def test_report_modified_source_rejected(self):
        r = report()
        r["source_commit"] = "c"*40
        with self.assertRaises(UHPContractError):
            assess_report(plan(), matrix(), r)

    def test_report_wrong_plan_rejected(self):
        r = report()
        r["plan_digest"] = "sha256:" + "a"*64
        with self.assertRaises(UHPContractError):
            assess_report(plan(), matrix(), r)

    def test_report_missing_probe_holds(self):
        r = report()
        r["probes"].pop()
        out = assess_report(plan(), matrix(), r)
        self.assertEqual(out["verdict"], "HOLD")
        self.assertIn("INCOMPLETE_OR_EXTRA_PROBE_REPORT", out["reasons"])

    def test_negative_probe_allowed_holds(self):
        r = report()
        r["probes"][0]["observed"] = "ALLOWED"
        out = assess_report(plan(), matrix(), r)
        self.assertEqual(out["verdict"], "HOLD")
        self.assertIn("NEGATIVE_PROBE_NOT_DENIED_AS_REQUIRED", out["reasons"])

    def test_missing_observer_evidence_ref_holds(self):
        r = report()
        r["probes"][0]["evidence_ref"] = None
        out = assess_report(plan(), matrix(), r)
        self.assertEqual(out["verdict"], "HOLD")
        self.assertIn("INDEPENDENT_PROOF_REFERENCE_MISSING", out["reasons"])

    def test_replay_probe_wrong_outcome_holds(self):
        r = report()
        for p in r["probes"]:
            if p["id"] == "N09":
                p["observed"] = "MATCH"
        self.assertEqual(assess_report(plan(), matrix(), r)["verdict"], "HOLD")

    def test_legacy_live_host_self_assertion_not_trusted(self):
        legacy = {"witness_origin": "LIVE_HOST",
                  "execution_id": "arbitrary", "status": "PASS"}
        review = assess_report(plan(), matrix(), report(), legacy)
        self.assertEqual(review["verdict"], "HOLD")
        self.assertIn("LEGACY_LIVE_HOST_LABEL_NOT_IDENTITY_PROOF", review["reasons"])
        self.assertFalse(review["independent_host_identity_verified"])

    def test_legacy_reference_not_upgraded(self):
        legacy = {"witness_origin": "REFERENCE_IMPLEMENTATION"}
        out = assess_report(plan(), matrix(), report(), legacy)
        self.assertFalse(out["independent_host_identity_verified"])

    def test_forged_authorization_in_plan_rejected(self):
        p = plan()
        p["dispatch_authorized"] = True
        with self.assertRaises(UHPContractError):
            assess_report(p, matrix(), report())

    def test_forged_promotion_in_plan_rejected(self):
        p = plan()
        p["promotion_authorized"] = True
        with self.assertRaises(UHPContractError):
            assess_report(p, matrix(), report())

    def test_tampered_matrix_does_not_match_plan(self):
        m = matrix()
        m["negative_probes"][0]["purpose"] = "anything"
        with self.assertRaises(UHPContractError):
            assess_report(plan(), m, report())

    def test_report_extra_result_rejected(self):
        r = report()
        r["probes"].append({"id": "N999", "observed": "MATCH", "evidence_ref": "extra"})
        self.assertEqual(assess_report(plan(), matrix(), r)["verdict"], "HOLD")

    def test_duplicate_report_rejected(self):
        r = report()
        r["probes"].append(copy.deepcopy(r["probes"][0]))
        with self.assertRaises(UHPContractError):
            assess_report(plan(), matrix(), r)

    def test_report_no_mutation(self):
        p,m,r = plan(),matrix(),report()
        old=copy.deepcopy((p,m,r))
        assess_report(p,m,r)
        self.assertEqual((p,m,r),old)

    def test_read_only_executor_cannot_claim_external_effects(self):
        r=assess_report(plan(),matrix(),report())
        self.assertFalse(r["external_effects_verified"])
        self.assertFalse(r["promotion_authorized"])

    def test_control_matrix_requires_host_separation(self):
        m=matrix()
        self.assertTrue(any("distinct principals" in x["requirement"]
                            for x in m["controls"]))
        self.assertTrue(any("independently controlled host" in x["requirement"]
                            for x in m["controls"]))

    def test_no_actual_host_or_network_execution(self):
        p=plan()
        self.assertEqual(p["proof_capture_mode"],"EXTERNAL_OBSERVER_REQUIRED")
        self.assertFalse(p["live_run_performed"])


if __name__ == "__main__":
    unittest.main()
