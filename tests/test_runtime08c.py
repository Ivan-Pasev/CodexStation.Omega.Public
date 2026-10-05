import copy
import unittest

from runtime08c.adapters import (
    adapt_dfpl_gateway_request,
    adapt_digital_fabrica_transition,
    adapt_gilc_effect_intent,
    adapt_highestone_state,
    adapt_neural_lattice_state,
)
from runtime08c.runtime import (
    compile_archetonic_plate,
    execute_transition,
    fold_events,
    make_conflict,
    make_state,
    plan_digest,
    recovery_check,
    verify_state,
)


def base_state():
    return make_state(
        project_id="p1",
        payload={"x": 1},
        grants=[
            {
                "grant_id": "g1",
                "principal_id": "actor:1",
                "level": "A2",
                "rights": ["cap:write"],
                "scope": ["*"],
            }
        ],
        provenance_refs=["genesis"],
    )


def invariant_pass():
    return [{"invariant_id": "inv:root", "status": "PASS", "evidence_refs": ["test"]}]


class Runtime08CTests(unittest.TestCase):
    def test_state_digest(self):
        s = base_state()
        self.assertTrue(verify_state(s))
        s["payload"]["x"] = 2
        self.assertFalse(verify_state(s))

    def test_valid_local_transition(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:1",
            project_id="p1",
            state=s,
            principal_id="actor:1",
            operations=[{"op": "SET", "key": "x", "value": 2}],
            required_authority=["A2"],
            protected_invariants=["inv:root"],
        )
        r = execute_transition(
            s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass()
        )
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["state"]["payload"]["x"], 2)
        self.assertEqual(r["state"]["revision"], 1)
        self.assertEqual(r["receipt"]["outcome"], "PASS")

    def test_stale_parent_holds(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:2", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "SET", "key": "x", "value": 3}],
            required_authority=["A2"], protected_invariants=["inv:root"],
        )
        t["parent_state_digest"] = {"algorithm": "sha256", "value": "0" * 64, "domain": "canonical-state"}
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        self.assertEqual(r["status"], "HOLD")
        self.assertIn("STALE_OR_FOREIGN_PARENT", r["receipt"]["decision_vector"]["admission"]["reasons"])

    def test_missing_invariant_holds(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:3", project_id="p1", state=s, principal_id="actor:1",
            operations=[], required_authority=["A2"], protected_invariants=["inv:root"],
        )
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=[])
        self.assertEqual(r["status"], "HOLD")

    def test_insufficient_predecessor_authority_holds(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:4", project_id="p1", state=s, principal_id="actor:1",
            operations=[], required_authority=["A4"], protected_invariants=["inv:root"],
        )
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        self.assertEqual(r["status"], "HOLD")
        self.assertIn("INSUFFICIENT_PREDECESSOR_AUTHORITY", r["receipt"]["decision_vector"]["admission"]["reasons"])

    def test_non_governance_authority_bootstrap_holds(self):
        s = base_state()
        grant = {"grant_id": "g2", "principal_id": "actor:1", "level": "A5", "rights": [], "scope": ["*"]}
        t = compile_archetonic_plate(
            plate_id="plate:5", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "GRANT", "grant": grant}],
            required_authority=["A2"], protected_invariants=["inv:root"], kind="OPERATIONAL",
        )
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        self.assertEqual(r["status"], "HOLD")
        self.assertIn("NON_GOVERNANCE_AUTHORITY_ESCALATION", r["receipt"]["decision_vector"]["admission"]["reasons"])

    def test_governance_can_mutate_grants_with_predecessor_authority(self):
        s = base_state()
        s["grants"][0]["level"] = "A5"
        s["digest"] = make_state(
            project_id=s["project_id"], state_id=s["state_id"], revision=s["revision"],
            payload=s["payload"], grants=s["grants"], provenance_refs=s["provenance_refs"]
        )["digest"]
        grant = {"grant_id": "g2", "principal_id": "actor:2", "level": "A2", "rights": [], "scope": ["*"]}
        t = compile_archetonic_plate(
            plate_id="plate:6", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "GRANT", "grant": grant}],
            required_authority=["A5"], protected_invariants=["inv:root"], kind="GOVERNANCE",
        )
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        self.assertEqual(r["status"], "PASS")
        self.assertTrue(any(g["grant_id"] == "g2" for g in r["state"]["grants"]))

    def test_plan_binding_mismatch_holds(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:7", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "SET", "key": "x", "value": 2}],
            required_authority=["A2"], protected_invariants=["inv:root"],
        )
        t["operations"].append({"op": "SET", "key": "y", "value": 3})
        self.assertNotEqual(t["authorized_plan_digest"], plan_digest(t))
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        self.assertEqual(r["status"], "HOLD")
        self.assertIn("AUTHORIZED_PLAN_BINDING_MISMATCH", r["receipt"]["decision_vector"]["admission"]["reasons"])

    def test_unknown_effect_is_preserved_and_no_successor(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:8", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "EFFECT", "effect_type": "external.write"}],
            required_authority=["A2"], protected_invariants=["inv:root"],
        )
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        self.assertEqual(r["status"], "UNKNOWN_OUTCOME")
        self.assertEqual(r["state"]["digest"], s["digest"])
        self.assertIsNone(r["receipt"]["after_digest"])

    def test_observed_effect_pass_allows_successor(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:9", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "EFFECT", "effect_type": "external.write"}],
            required_authority=["A2"], protected_invariants=["inv:root"],
        )
        r = execute_transition(
            s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass(),
            effect_executor=lambda op: {"status": "PASS", "observed": True},
        )
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["state"]["revision"], 1)

    def test_replay_determinism(self):
        s = base_state()
        t1 = compile_archetonic_plate(
            plate_id="plate:r1", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "SET", "key": "x", "value": 2}],
            required_authority=["A2"], protected_invariants=["inv:root"],
        )
        r1 = execute_transition(s, t1, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        t2 = compile_archetonic_plate(
            plate_id="plate:r2", project_id="p1", state=r1["state"], principal_id="actor:1",
            operations=[{"op": "SET", "key": "y", "value": 3}],
            required_authority=["A2"], protected_invariants=["inv:root"],
        )
        seq = [
            {"transition": t1, "semantic_decision": {"status": "ALLOW"}, "invariant_results": invariant_pass()},
            {"transition": t2, "semantic_decision": {"status": "ALLOW"}, "invariant_results": invariant_pass()},
        ]
        a = fold_events(s, copy.deepcopy(seq))
        b = fold_events(s, copy.deepcopy(seq))
        self.assertEqual(a["state"]["digest"], b["state"]["digest"])
        self.assertEqual(a["events"], b["events"])

    def test_recovery_check(self):
        s = base_state()
        t = compile_archetonic_plate(
            plate_id="plate:rec", project_id="p1", state=s, principal_id="actor:1",
            operations=[{"op": "SET", "key": "x", "value": 2}],
            required_authority=["A2"], protected_invariants=["inv:root"],
        )
        r = execute_transition(s, t, semantic_decision={"status": "ALLOW"}, invariant_results=invariant_pass())
        ok = recovery_check(s, r["state"], r["receipt"])
        self.assertEqual(ok["status"], "RECOVERABLE")
        bad = copy.deepcopy(r["receipt"])
        bad["after_digest"] = s["digest"]
        self.assertEqual(recovery_check(s, r["state"], bad)["status"], "QUARANTINE")

    def test_conflict_is_durable_object(self):
        c = make_conflict(conflict_id="c1", conflict_type="MODEL_SELECTION_CONFLICT", participants=["a", "b"])
        self.assertEqual(c["status"], "OPEN")
        self.assertEqual(c["participants"], ["a", "b"])

    def test_digital_fabrica_adapter(self):
        s = base_state()
        src = {
            "transition_id": "df:1", "parent_state_digest": s["digest"], "actor_id": "actor:1",
            "operations": [], "required_authority": ["A2"], "protected_invariants": ["inv:root"]
        }
        t = adapt_digital_fabrica_transition(src, project_id="p1")
        self.assertEqual(t["source_profile"], "DIGITAL_FABRICA_CORE")
        self.assertEqual(t["parent_state_digest"], s["digest"])

    def test_dfpl_adapter_preserves_plan_binding(self):
        s = base_state()
        request = {"request_id": "dfpl:1", "parent_state_digest": s["digest"], "operations": []}
        auth = {"principal_id": "actor:1", "required_capabilities": ["cap:write"], "plan_digest": plan_digest({"operations": []})}
        t = adapt_dfpl_gateway_request(request, auth, project_id="p1")
        self.assertEqual(t["authorized_plan_digest"], auth["plan_digest"])

    def test_highestone_adapter(self):
        s = adapt_highestone_state(
            {"rootId": 1, "branchId": 2, "revision": 3, "grants": [{"actor": "actor:1", "level": 2}]},
            project_id="p1",
        )
        self.assertEqual(s["revision"], 3)
        self.assertTrue(verify_state(s))

    def test_gilc_effect_adapter(self):
        s = base_state()
        t = adapt_gilc_effect_intent(
            {"intent_id": "e1", "principal_id": "actor:1", "effect_type": "write", "required_authority": "A2"},
            s, project_id="p1"
        )
        self.assertEqual(t["operations"][0]["op"], "EFFECT")

    def test_neural_lattice_adapter(self):
        s = adapt_neural_lattice_state(
            {"id": "cell:1", "version": 2, "status": "ACTIVE", "state": {"x": 1}, "provenance": ["p"], "conflictStatus": "OPEN"},
            project_id="p1"
        )
        self.assertEqual(s["revision"], 2)
        self.assertEqual(len(s["conflicts"]), 1)


if __name__ == "__main__":
    unittest.main()
