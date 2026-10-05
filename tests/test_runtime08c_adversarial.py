import copy, unittest
from runtime08c.runtime import compile_archetonic_plate, execute_transition, fold_events, make_state

def state():
    return make_state(
        project_id="p",
        payload={"x":1},
        grants=[{"grant_id":"g","principal_id":"a","level":"A2","rights":["cap:write"],"scope":["*"]}],
        provenance_refs=["test"],
    )

def inv(status="PASS"):
    return [{"invariant_id":"i","status":status,"evidence_refs":["test"]}]

def plate(s, ops=None, auth=None, kind="OPERATIONAL"):
    return compile_archetonic_plate(
        plate_id="adv",project_id="p",state=s,principal_id="a",
        operations=ops or [],required_authority=auth or ["A2"],
        protected_invariants=["i"],kind=kind
    )

class Runtime08CAdversarialTests(unittest.TestCase):
    def test_semantic_deny_holds(self):
        s=state(); t=plate(s)
        r=execute_transition(s,t,semantic_decision={"status":"DENY"},invariant_results=inv())
        self.assertEqual(r["status"],"HOLD")

    def test_tampered_current_state_holds(self):
        s=state(); s["payload"]["x"]=99; t=plate(s)
        r=execute_transition(s,t,semantic_decision={"status":"ALLOW"},invariant_results=inv())
        self.assertEqual(r["status"],"HOLD")
        self.assertIn("CURRENT_STATE_DIGEST_INVALID",r["receipt"]["decision_vector"]["admission"]["reasons"])

    def test_project_substitution_holds(self):
        s=state(); t=plate(s); t["project_id"]="other"
        r=execute_transition(s,t,semantic_decision={"status":"ALLOW"},invariant_results=inv())
        self.assertEqual(r["status"],"HOLD")
        self.assertIn("PROJECT_MISMATCH",r["receipt"]["decision_vector"]["admission"]["reasons"])

    def test_failed_protected_invariant_holds(self):
        s=state(); t=plate(s)
        r=execute_transition(s,t,semantic_decision={"status":"ALLOW"},invariant_results=inv("FAIL"))
        self.assertEqual(r["status"],"HOLD")

    def test_required_right_is_not_inferred_from_level(self):
        s=state(); t=plate(s,auth=["cap:admin"])
        r=execute_transition(s,t,semantic_decision={"status":"ALLOW"},invariant_results=inv())
        self.assertEqual(r["status"],"HOLD")

    def test_unsupported_local_operation_fails_closed(self):
        s=state(); t=plate(s,ops=[{"op":"MAGIC","value":1}])
        r=execute_transition(s,t,semantic_decision={"status":"ALLOW"},invariant_results=inv())
        self.assertEqual(r["status"],"FAIL")
        self.assertEqual(r["state"]["digest"],s["digest"])

    def test_unrecognized_effect_executor_status_becomes_unknown(self):
        s=state(); t=plate(s,ops=[{"op":"EFFECT","effect_type":"x"}])
        r=execute_transition(s,t,semantic_decision={"status":"ALLOW"},invariant_results=inv(),
                             effect_executor=lambda op:{"status":"MAYBE"})
        self.assertEqual(r["status"],"UNKNOWN_OUTCOME")
        self.assertEqual(r["state"]["digest"],s["digest"])

    def test_fold_stops_at_first_hold(self):
        s=state()
        t1=plate(s,ops=[{"op":"SET","key":"x","value":2}])
        first=execute_transition(s,t1,semantic_decision={"status":"ALLOW"},invariant_results=inv())
        t2=plate(first["state"],ops=[{"op":"SET","key":"y","value":3}])
        seq=[
          {"transition":t1,"semantic_decision":{"status":"ALLOW"},"invariant_results":inv()},
          {"transition":t2,"semantic_decision":{"status":"DENY"},"invariant_results":inv()},
        ]
        r=fold_events(s,copy.deepcopy(seq))
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["state"]["payload"]["x"],2)
        self.assertNotIn("y",r["state"]["payload"])

if __name__=="__main__":
    unittest.main()
