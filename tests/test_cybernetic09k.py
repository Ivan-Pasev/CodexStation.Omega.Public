import unittest
from cybernetic09k.reconciler import schedule,evidence_requirements,stable_without_delta

class Cybernetic09KTests(unittest.TestCase):
    def test_external_gates_wait_without_new_evidence(self):
        s=schedule()
        self.assertIn("08I_RESTRICTED_EXECUTION_RECEIPTS",s["waiting_for_evidence"])
        self.assertIn("09J_LIVE_HOST_RETURNS",s["waiting_for_evidence"])

    def test_license_requests_governance(self):
        s=schedule()
        self.assertIn("LICENSE_IP_REVIEW",s["governance_pending"])
        self.assertEqual(s["next_action"],"GOVERNANCE:LICENSE_IP_REVIEW")

    def test_new_08i_evidence_resumes_only_that_gate(self):
        s=schedule(evidence_deltas={"08I_RESTRICTED_EXECUTION_RECEIPTS":True})
        self.assertEqual(s["resumable"][0],"08I_RESTRICTED_EXECUTION_RECEIPTS")
        self.assertEqual(s["next_action"],"RESUME:08I_RESTRICTED_EXECUTION_RECEIPTS")

    def test_new_09j_return_resumes_host_ingestion(self):
        s=schedule(evidence_deltas={"09J_LIVE_HOST_RETURNS":True})
        self.assertIn("09J_LIVE_HOST_RETURNS",s["resumable"])

    def test_requirements_are_explicit(self):
        r=evidence_requirements("DFPL_PRIMA_FULL_RUNTIME_REPRODUCTION")
        self.assertEqual(r["status"],"KNOWN")
        self.assertTrue(r["minimal_admissible_evidence"])

    def test_no_delta_is_stable(self):
        self.assertTrue(stable_without_delta())

if __name__=="__main__":
    unittest.main()
