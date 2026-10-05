import copy,json,unittest
from pathlib import Path
from cybernetic09g.conformance import classify_witness,ingest,aggregate,expected_profile_digest

ROOT=Path(__file__).resolve().parents[1]
REG=json.loads((ROOT/"cybernetic09g/LIVE_CONFORMANCE_REGISTRY.json").read_text())
POLICY="2c1cff5173ed8cb36a037c34ba030416af14c5c084ddccf47d9ee6241e9b0ea7"

def witness(host="chatgpt-codex",origin="LIVE_HOST",status="PASS"):
    return {
      "schema":"GILC/CODEXSTATION/OMEGA-LIVE-HOST-WITNESS/0.9g",
      "host_id":host,
      "host_profile_digest":expected_profile_digest(host),
      "active_policy_digest":POLICY,
      "policy_version":1,
      "replay_policy_digest":POLICY,
      "routing_order":["cs.skill::source-audit::v0.1","cs.skill::adversarial-review::v0.1"],
      "summary_digest":"summary",
      "environment":{"runtime":"fixture","runtime_version":"1","adapter_version":"1","capability_observations":[]},
      "witness_origin":origin,
      "execution_id":"exec-1",
      "status":status
    }

class Cybernetic09GTests(unittest.TestCase):
    def test_live_witness_passes(self):
        self.assertEqual(classify_witness(witness())["status"],"LIVE_CONFORMANCE_PASS")

    def test_reference_witness_cannot_close_live_gate(self):
        self.assertEqual(classify_witness(witness(origin="REFERENCE_IMPLEMENTATION"))["status"],"HOLD_NON_LIVE_WITNESS")

    def test_policy_mismatch_rejected(self):
        w=witness(); w["replay_policy_digest"]="0"*64
        self.assertEqual(classify_witness(w)["status"],"REJECT_INVALID_WITNESS")

    def test_profile_mismatch_rejected(self):
        w=witness(); w["host_profile_digest"]="0"*64
        self.assertEqual(classify_witness(w)["status"],"REJECT_INVALID_WITNESS")

    def test_missing_witness_is_hold_not_fail(self):
        self.assertEqual(aggregate(REG)["status"],"HOLD_NO_COMPLETE_LIVE_HOST_WITNESSES")

    def test_two_live_hosts_close_gate(self):
        r,_=ingest(REG,witness("chatgpt-codex"))
        g=witness("gemini-notebook"); g["execution_id"]="exec-2"
        r,_=ingest(r,g)
        self.assertEqual(aggregate(r)["status"],"LIVE_MULTI_HOST_CONFORMANCE_PASS")

    def test_unknown_outcome_holds(self):
        r,_=ingest(REG,witness("chatgpt-codex",status="UNKNOWN_OUTCOME"))
        self.assertEqual(r["hosts"]["chatgpt-codex"]["state"],"HOLD_HOST_UNKNOWN_OUTCOME")

if __name__=="__main__":
    unittest.main()
