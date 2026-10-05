import copy,json,unittest
from pathlib import Path
from cybernetic09f.distributor import distribute,compare_receipts,tamper_receipt
from cybernetic09d.crystallizer import POLICY

ROOT=Path(__file__).resolve().parents[1]
REG=json.loads((ROOT/"cybernetic09e/ACTIVE_POLICY_REGISTRY.json").read_text())
TELEMETRY=json.loads((ROOT/"cybernetic09d/REFERENCE_TELEMETRY.json").read_text())["records"]
CANDIDATES=[
 {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
 {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"}
]

class Cybernetic09FTests(unittest.TestCase):
    def test_hosts_share_policy_and_replay_semantics(self):
        a=distribute("chatgpt-codex",REG,POLICY,TELEMETRY,CANDIDATES)
        b=distribute("gemini-notebook",REG,POLICY,TELEMETRY,CANDIDATES)
        self.assertEqual(a["status"],"PARITY_PASS")
        self.assertEqual(b["status"],"PARITY_PASS")
        self.assertEqual(compare_receipts([a,b])["status"],"PARITY_PASS")
        self.assertNotEqual(a["host_profile_digest"],b["host_profile_digest"])

    def test_host_profile_difference_is_not_canon_fork(self):
        a=distribute("chatgpt-codex",REG,POLICY,TELEMETRY,CANDIDATES)
        b=distribute("gemini-notebook",REG,POLICY,TELEMETRY,CANDIDATES)
        self.assertEqual(a["active_policy_digest"],b["active_policy_digest"])
        self.assertEqual(a["routing_order"],b["routing_order"])

    def test_routing_divergence_holds(self):
        a=distribute("chatgpt-codex",REG,POLICY,TELEMETRY,CANDIDATES)
        b=distribute("gemini-notebook",REG,POLICY,TELEMETRY,CANDIDATES)
        b=tamper_receipt(b,routing_order=list(reversed(b["routing_order"])))
        self.assertEqual(compare_receipts([a,b])["status"],"HOLD_DIVERGENCE")
        self.assertIn("ROUTING_ORDER_DIVERGENCE",compare_receipts([a,b])["reasons"])

    def test_policy_digest_divergence_holds(self):
        a=distribute("chatgpt-codex",REG,POLICY,TELEMETRY,CANDIDATES)
        b=distribute("gemini-notebook",REG,POLICY,TELEMETRY,CANDIDATES)
        b=tamper_receipt(b,replay_policy_digest="0"*64)
        self.assertEqual(compare_receipts([a,b])["status"],"HOLD_DIVERGENCE")

    def test_unknown_host_holds(self):
        r=distribute("unknown-host",REG,POLICY,TELEMETRY,CANDIDATES)
        self.assertEqual(r["status"],"HOLD_PROFILE_INVALID")

if __name__=="__main__":
    unittest.main()
