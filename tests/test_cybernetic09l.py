import copy,json,unittest
from pathlib import Path
from cybernetic09l.governance import authorize_decision,decision_digest,compute_release_readiness

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"MANIFEST.json").read_text())
DECISION=json.loads((ROOT/"cybernetic09l/LICENSE_IP_DECISION.json").read_text())

def auth():
    return {
      "authorization_id":"synthetic-auth",
      "principal_id":"governor-test",
      "authority_level":"A3",
      "rights":["GOVERNANCE_DECIDE"],
      "decision_digest":decision_digest(DECISION)
    }

class Cybernetic09LTests(unittest.TestCase):
    def test_proposed_decision_not_authorized(self):
        out,v=authorize_decision(DECISION,{})
        self.assertEqual(v["status"],"HOLD")
        self.assertEqual(out["state"],"PROPOSED")

    def test_synthetic_authorization_can_exercise_path(self):
        out,v=authorize_decision(DECISION,auth())
        self.assertEqual(v["status"],"AUTHORIZED")
        self.assertEqual(out["state"],"AUTHORIZED")

    def test_authorized_license_still_not_release_eligible(self):
        out,_=authorize_decision(DECISION,auth())
        r=compute_release_readiness(MANIFEST,out)
        self.assertFalse(r["release_eligible"])
        self.assertTrue(r["external_frontier_blockers"])

    def test_without_authorization_license_gate_blocks(self):
        r=compute_release_readiness(MANIFEST,None)
        self.assertFalse(r["release_eligible"])
        self.assertTrue(any(x["gate"]=="license_ip_review" for x in r["publication_gate_blockers"]))

    def test_decision_does_not_close_external_frontiers(self):
        out,_=authorize_decision(DECISION,auth())
        r=compute_release_readiness(MANIFEST,out)
        self.assertIn("08I_RESTRICTED_EXECUTION_RECEIPTS",r["external_frontier_blockers"])
        self.assertIn("09J_LIVE_HOST_RETURNS",r["external_frontier_blockers"])

if __name__=="__main__":
    unittest.main()
