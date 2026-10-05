import unittest
from cybernetic09a.controller import cycle

class Cybernetic09ATests(unittest.TestCase):
    def test_blocked_high_priority_does_not_starve_admissible(self):
        r=cycle(grants=["A0"])
        self.assertEqual(r["selection"]["mission"]["id"],"mission.09a.cybernetic-self-validation")
        self.assertEqual(r["status"],"VERIFIED")

    def test_capability_does_not_create_grant(self):
        missions=[{
          "id":"m","priority":1,"intent":"x",
          "required_capabilities":["cap.mutate.public_repo"],
          "required_authority":["A4"],"mode":"LOCAL_VERIFICATION"
        }]
        r=cycle(grants=["A0"],missions=missions)
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["frontier"][0]["status"],"HELD_AUTHORITY")

    def test_unobserved_capability_holds(self):
        missions=[{
          "id":"m","priority":1,"intent":"x",
          "required_capabilities":["cap.external_effect.confirmed"],
          "required_authority":["A0"],"mode":"EXTERNAL_VERIFICATION"
        }]
        r=cycle(grants=["A0"],missions=missions)
        self.assertEqual(r["status"],"HOLD")
        self.assertEqual(r["frontier"][0]["status"],"HELD_CAPABILITY")

    def test_external_without_executor_is_unknown(self):
        missions=[{
          "id":"m","priority":1,"intent":"x",
          "required_capabilities":["cap.external_effect.confirmed"],
          "required_authority":["A0"],"mode":"EXTERNAL_VERIFICATION"
        }]
        r=cycle(grants=["A0"],missions=missions,capability_overrides={"cap.external_effect.confirmed":"OBSERVED"})
        self.assertEqual(r["status"],"UNKNOWN_OUTCOME")

    def test_learning_keeps_zero_delta(self):
        r=cycle(grants=["A0"])
        self.assertEqual(r["model"]["authority_delta"],"NONE")
        self.assertEqual(r["model"]["mission_stats"]["mission.09a.cybernetic-self-validation"]["verified"],1)

if __name__=="__main__":
    unittest.main()
