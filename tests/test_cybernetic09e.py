import copy,json,unittest
from pathlib import Path
from cybernetic09d.crystallizer import propose_policy_update,rank_admissible,POLICY
from cybernetic09e.governor import validate_proposal,promote,rollback_policy,digest,policy_digest

ROOT=Path(__file__).resolve().parents[1]
TELEMETRY=json.loads((ROOT/"cybernetic09d/REFERENCE_TELEMETRY.json").read_text())["records"]
REGISTRY=json.loads((ROOT/"cybernetic09e/ACTIVE_POLICY_REGISTRY.json").read_text())
CANDIDATES=[
 {"skill_uri":"cs.skill::source-audit::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"},
 {"skill_uri":"cs.skill::adversarial-review::v0.1","admissible":True,"authority_ceiling":"A1","evidence_ceiling":"IMPLEMENTATION"}
]

def fixture():
    current=copy.deepcopy(POLICY)
    proposal=propose_policy_update(TELEMETRY,current)["proposal"]
    ranked=rank_admissible(CANDIDATES,TELEMETRY,proposal)
    witness={"policy_digest":ranked["policy_digest"],"routing_order":ranked["routing_order"],"summary_digest":digest(ranked["summary"])}
    auth={
      "authorization_id":"synthetic-auth",
      "principal_id":"governor-test",
      "authority_level":"A3",
      "rights":["POLICY_PROMOTE"],
      "proposal_digest":policy_digest(proposal),
      "predecessor_policy_digest":policy_digest(current)
    }
    return current,proposal,witness,auth

class Cybernetic09ETests(unittest.TestCase):
    def test_valid_governed_proposal_promotes(self):
        current,proposal,witness,auth=fixture()
        reg,result=promote(REGISTRY,current,proposal,TELEMETRY,CANDIDATES,witness,auth)
        self.assertEqual(result["status"],"PROMOTED")
        self.assertEqual(reg["active_policy"]["policy_version"],2)
        self.assertEqual(reg["rollback_pointer"]["policy_version"],1)

    def test_missing_authorization_holds(self):
        current,proposal,witness,_=fixture()
        v=validate_proposal(current,proposal,TELEMETRY,CANDIDATES,witness,{})
        self.assertEqual(v["status"],"HOLD")
        self.assertIn("AUTHORIZATION_MISSING",v["reasons"])

    def test_predecessor_mismatch_holds(self):
        current,proposal,witness,auth=fixture()
        proposal["derived_from_policy_digest"]="0"*64
        v=validate_proposal(current,proposal,TELEMETRY,CANDIDATES,witness,auth)
        self.assertEqual(v["status"],"HOLD")
        self.assertIn("PREDECESSOR_POLICY_IDENTITY_FAIL",v["reasons"])

    def test_protected_semantics_change_holds(self):
        current,proposal,witness,auth=fixture()
        proposal["scope"]="UNBOUNDED"
        auth["proposal_digest"]=policy_digest(proposal)
        v=validate_proposal(current,proposal,TELEMETRY,CANDIDATES,witness,auth)
        self.assertEqual(v["status"],"HOLD")
        self.assertIn("PROTECTED_POLICY_SEMANTICS_CHANGED",v["reasons"])

    def test_replay_witness_mismatch_holds(self):
        current,proposal,witness,auth=fixture()
        witness["routing_order"]=list(reversed(witness["routing_order"]))
        v=validate_proposal(current,proposal,TELEMETRY,CANDIDATES,witness,auth)
        self.assertEqual(v["status"],"HOLD")
        self.assertIn("ROUTING_ORDER_MISMATCH",v["reasons"])

    def test_policy_rollback_is_policy_scope_only(self):
        current,proposal,witness,auth=fixture()
        reg,result=promote(REGISTRY,current,proposal,TELEMETRY,CANDIDATES,witness,auth)
        self.assertEqual(result["status"],"PROMOTED")
        rolled,rr=rollback_policy(reg,authorization=auth)
        self.assertEqual(rr["status"],"ROLLED_BACK")
        self.assertEqual(rr["scope"],"ROUTING_POLICY_ONLY")
        self.assertEqual(rolled["active_policy"]["policy_version"],1)

if __name__=="__main__":
    unittest.main()
