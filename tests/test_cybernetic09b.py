import unittest
from cybernetic09b.compiler import compile_plan,execute_plan,critique,recovery_decision
from runtime08c.runtime import make_state

def state():
    return make_state(project_id="p09b",grants=[{"grant_id":"g","principal_id":"actor","level":"A0","rights":[],"scope":["*"]}])

class Cybernetic09BTests(unittest.TestCase):
    def test_local_plan_executes_through_runtime(self):
        mission={"id":"m.local","intent":"set x","mode":"LOCAL_VERIFICATION","required_capabilities":["cap.execute.public_ci"],"required_authority":["A0"]}
        plan=compile_plan(mission,project_id="p09b",principal_id="actor",local_operations=[{"op":"SET","key":"x","value":1}],protected_invariants=["inv"],reversibility="REVERSIBLE")
        r=execute_plan(plan,state=state(),capability_state={"cap.execute.public_ci":"OBSERVED"},grants=["A0"],invariant_results=[{"invariant_id":"inv","status":"PASS","evidence_refs":["t"]}])
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(r["state"]["payload"]["x"],1)

    def test_external_without_receipt_is_unknown(self):
        mission={"id":"m.effect","intent":"effect","mode":"EXTERNAL_VERIFICATION","required_capabilities":["cap.external_effect.confirmed"],"required_authority":["A0"]}
        plan=compile_plan(mission,project_id="p09b",principal_id="actor",external_effects=[{"kind":"E","target":"x"}])
        r=execute_plan(plan,state=state(),capability_state={"cap.external_effect.confirmed":"OBSERVED"},grants=["A0"],invariant_results=[])
        self.assertEqual(r["status"],"UNKNOWN_OUTCOME")
        self.assertIn("EXTERNAL_EFFECT_NOT_CLOSED",critique(plan,r)["issues"])

    def test_matching_effect_receipt_closes(self):
        mission={"id":"m.effect","intent":"effect","mode":"EXTERNAL_VERIFICATION","required_capabilities":["cap.external_effect.confirmed"],"required_authority":["A0"]}
        plan=compile_plan(mission,project_id="p09b",principal_id="actor",external_effects=[{"kind":"E","target":"x"}])
        effect_id=plan["external_effects"][0]["effect_id"]
        receipt={"effect_id":effect_id,"plan_digest":plan["plan_digest"],"status":"PASS","observer":"independent:test","evidence_refs":["e1"]}
        r=execute_plan(plan,state=state(),capability_state={"cap.external_effect.confirmed":"OBSERVED"},grants=["A0"],invariant_results=[],effect_receipts=[receipt])
        self.assertEqual(r["status"],"PASS")

    def test_mismatched_receipt_holds(self):
        mission={"id":"m.effect","intent":"effect","mode":"EXTERNAL_VERIFICATION","required_capabilities":["cap.external_effect.confirmed"],"required_authority":["A0"]}
        plan=compile_plan(mission,project_id="p09b",principal_id="actor",external_effects=[{"kind":"E","target":"x"}])
        receipt={"effect_id":"wrong","plan_digest":plan["plan_digest"],"status":"PASS","observer":"independent:test","evidence_refs":["e1"]}
        r=execute_plan(plan,state=state(),capability_state={"cap.external_effect.confirmed":"OBSERVED"},grants=["A0"],invariant_results=[],effect_receipts=[receipt])
        self.assertEqual(r["status"],"UNKNOWN_OUTCOME")

    def test_capability_and_authority_both_required(self):
        mission={"id":"m","intent":"x","mode":"LOCAL_VERIFICATION","required_capabilities":["cap.execute.public_ci"],"required_authority":["A2"]}
        plan=compile_plan(mission,project_id="p09b",principal_id="actor")
        r=execute_plan(plan,state=state(),capability_state={"cap.execute.public_ci":"OBSERVED"},grants=["A0"],invariant_results=[])
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["reason"],"AUTHORITY_BINDING_FAILED")

    def test_recovery_never_claims_external_rollback(self):
        mission={"id":"m","intent":"x","mode":"EXTERNAL_VERIFICATION","required_capabilities":[],"required_authority":[]}
        plan=compile_plan(mission,project_id="p09b",principal_id="actor",external_effects=[{"kind":"E"}],reversibility="REVERSIBLE")
        predecessor=state()
        result={"status":"UNKNOWN_OUTCOME","phase":"EFFECT","state":predecessor}
        d=recovery_decision(plan,result,predecessor)
        self.assertEqual(d["status"],"QUARANTINE")

if __name__=="__main__":
    unittest.main()
