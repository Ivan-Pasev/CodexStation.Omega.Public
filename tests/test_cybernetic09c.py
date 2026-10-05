import unittest
from cybernetic09c.orchestrator import orchestrate,bind_skill,topological_steps,fallback_allowed,SKILLS
from runtime08c.runtime import make_state

def base_state():
    return make_state(project_id="p09c",grants=[{"grant_id":"g","principal_id":"actor","level":"A3","rights":[],"scope":["*"]}])

CAPS={
 "cap.observe.public_repo":"OBSERVED",
 "cap.simulate.reference_runtime":"OBSERVED",
 "cap.execute.public_ci":"OBSERVED",
 "cap.mutate.public_repo":"OBSERVED"
}

class Cybernetic09CTests(unittest.TestCase):
    def test_dependency_order(self):
        ordered=topological_steps([
          {"step_id":"b","depends_on":["a"]},{"step_id":"a","depends_on":[]}
        ])
        self.assertEqual([x["step_id"] for x in ordered],["a","b"])

    def test_skill_binding_requires_qualification_capability_and_authority(self):
        step={"step_id":"s","intent":"repository mutation","skill_uri":"cs.skill::repository-mutation::v0.1","required_authority":["A3"]}
        self.assertEqual(bind_skill(step,CAPS,["A3"])["status"],"PASS")
        self.assertEqual(bind_skill(step,{"cap.mutate.public_repo":"UNOBSERVED"},["A3"])["status"],"HOLD")
        self.assertEqual(bind_skill(step,CAPS,["A0"])["status"],"HOLD")

    def test_two_step_dag_executes(self):
        steps=[
          {"step_id":"audit","intent":"source audit","skill_uri":"cs.skill::source-audit::v0.1","depends_on":[],"required_capabilities":["cap.observe.public_repo"],"required_authority":["A0"],"mode":"LOCAL_VERIFICATION"},
          {"step_id":"mutate","intent":"repository mutation","skill_uri":"cs.skill::repository-mutation::v0.1","depends_on":["audit"],"required_capabilities":["cap.mutate.public_repo"],"required_authority":["A2"],"mode":"LOCAL_VERIFICATION","local_operations":[{"op":"SET","key":"done","value":True}],"reversibility":"REVERSIBLE"}
        ]
        r=orchestrate(project_id="p09c",principal_id="actor",steps=steps,state=base_state(),capability_state=CAPS,grants=["A0","A2","A3"])
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(r["state"]["payload"]["done"],True)

    def test_external_unknown_quarantines(self):
        steps=[{"step_id":"e","intent":"migration witness","skill_uri":"cs.skill::migration-witness::v0.1","depends_on":[],"required_capabilities":["cap.simulate.reference_runtime"],"required_authority":["A0"],"mode":"EXTERNAL_VERIFICATION","external_effects":[{"kind":"EXTERNAL"}],"reversibility":"REVERSIBLE"}]
        r=orchestrate(project_id="p09c",principal_id="actor",steps=steps,state=base_state(),capability_state=CAPS,grants=["A0"])
        self.assertEqual(r["status"],"QUARANTINE")
        self.assertEqual(r["step_status"]["e"],"QUARANTINE")

    def test_fallback_cannot_raise_authority_or_evidence(self):
        primary=SKILLS["cs.skill::repository-mutation::v0.1"]
        low=SKILLS["cs.skill::source-audit::v0.1"]
        self.assertTrue(fallback_allowed(primary,low))
        self.assertFalse(fallback_allowed(low,primary))

    def test_telemetry_never_changes_authority(self):
        steps=[{"step_id":"a","intent":"source audit","skill_uri":"cs.skill::source-audit::v0.1","depends_on":[],"required_capabilities":["cap.observe.public_repo"],"required_authority":["A0"],"mode":"LOCAL_VERIFICATION"}]
        r=orchestrate(project_id="p09c",principal_id="actor",steps=steps,state=base_state(),capability_state=CAPS,grants=["A0"])
        self.assertEqual(r["authority_delta"],"NONE")
        self.assertEqual(r["telemetry"][0]["status"],"PASS")

if __name__=="__main__":
    unittest.main()
