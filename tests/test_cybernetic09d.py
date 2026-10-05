import copy, json, unittest
from pathlib import Path
from cybernetic09d.crystallizer import summarize,rank_admissible,propose_policy_update,replay,crystallize_failure_patterns,POLICY

ROOT=Path(__file__).resolve().parents[1]
RECORDS=json.loads((ROOT/"cybernetic09d/REFERENCE_TELEMETRY.json").read_text())["records"]

class Cybernetic09DTests(unittest.TestCase):
    def test_health_signals_do_not_change_qualification(self):
        summary=summarize(RECORDS)
        self.assertEqual(summary["cs.skill::source-audit::v0.1"]["health"],"HEALTHY")
        self.assertEqual(summary["cs.skill::adversarial-review::v0.1"]["health"],"DEGRADED")

    def test_ranking_only_uses_admissible_candidates(self):
        candidates=[
          {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
          {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
          {"skill_uri":"forbidden","admissible":False,"authority_ceiling":"A5","evidence_ceiling":"SCIENTIFIC"}
        ]
        r=rank_admissible(candidates,RECORDS)
        self.assertEqual(r["routing_order"][0],"cs.skill::source-audit::v0.1")
        self.assertNotIn("forbidden",r["routing_order"])
        self.assertEqual(r["authority_delta"],"NONE")

    def test_policy_update_is_proposal_only(self):
        p=propose_policy_update(RECORDS)
        self.assertEqual(p["status"],"PROPOSAL_ONLY")
        self.assertIn("cs.skill::adversarial-review::v0.1",p["proposal"]["advisory_skill_watchlist"])
        self.assertEqual(p["authority_delta"],"NONE")

    def test_deterministic_replay(self):
        candidates=[
          {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True},
          {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True}
        ]
        self.assertTrue(replay(RECORDS,candidates,copy.deepcopy(POLICY))["deterministic"])

    def test_failure_patterns_are_advisory(self):
        pats=crystallize_failure_patterns(RECORDS)
        self.assertTrue(pats)
        self.assertTrue(all(p["advisory_only"] for p in pats))

    def test_no_samples_mean_unknown_not_bad(self):
        s=summarize([])
        self.assertEqual(s,{})

if __name__=="__main__":
    unittest.main()
