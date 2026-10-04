import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "OMEGA_REGISTRY.json"

class OmegaRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_authority_delta_none(self):
        self.assertEqual(self.registry["authority_delta"], "NONE")

    def test_object_ids_unique(self):
        ids = [x["id"] for x in self.registry["objects"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_relation_endpoints_exist(self):
        ids = {x["id"] for x in self.registry["objects"]}
        for rel in self.registry["relations"]:
            self.assertIn(rel["from"], ids)
            self.assertIn(rel["to"], ids)

    def test_noncollapse_endpoints_exist(self):
        ids = {x["id"] for x in self.registry["objects"]}
        for rule in self.registry["noncollapse"]:
            self.assertIn(rule["lhs"], ids)
            self.assertIn(rule["rhs"], ids)

    def test_status_model_is_multiaxial(self):
        self.assertEqual(
            set(self.registry["status_model"]),
            {"formal", "empirical", "execution", "reproduction", "implementation", "publication", "canon"},
        )

    def test_theorem_targets_are_not_silent_proofs(self):
        for theorem in self.registry["theorematic_objects"]:
            if theorem["class"] == "THEOREM_TARGET":
                self.assertNotIn(theorem["proof_status"], {"MACHINE_CHECKED", "INDEPENDENT_CHECKED"})

    def test_blocking_gates_preserved(self):
        gates = {g["id"]: g["status"] for g in self.registry["gates"]}
        self.assertEqual(gates["gate::license-ip-review"], "OPEN")
        self.assertEqual(gates["gate::full-private-corpus-publication"], "HOLD")
        self.assertEqual(gates["gate::nb00-live-conformance"], "OPEN")
        self.assertEqual(gates["gate::rgt04-clean-chat"], "OPEN")

    def test_validator_passes(self):
        run = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "validate_registry.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["authority_delta"], "NONE")

if __name__ == "__main__":
    unittest.main()
