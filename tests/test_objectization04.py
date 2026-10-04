import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "registry" / "objectization04"

class Objectization04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objects = json.loads((BASE / "OBJECTS.json").read_text(encoding="utf-8"))
        cls.prov = json.loads((BASE / "PROVENANCE.json").read_text(encoding="utf-8"))
        cls.rel = json.loads((BASE / "RELATIONS.json").read_text(encoding="utf-8"))
        cls.neg = json.loads((BASE / "NEGATIVE_HOLD.json").read_text(encoding="utf-8"))
        cls.skills = json.loads((BASE / "SKILLS.json").read_text(encoding="utf-8"))
        cls.deps = json.loads((BASE / "THEOREM_DEPENDENCIES.json").read_text(encoding="utf-8"))

    def test_twelve_semantic_objects(self):
        ids = [x["id"] for x in self.objects["objects"]]
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(ids), len(set(ids)))

    def test_provenance_covers_every_object(self):
        object_ids = {x["id"] for x in self.objects["objects"]}
        mapped = {x["object_id"] for x in self.prov["mappings"]}
        self.assertEqual(mapped, object_ids)

    def test_relations_stay_inside_object_set(self):
        object_ids = {x["id"] for x in self.objects["objects"]}
        for rel in self.rel["relations"]:
            self.assertIn(rel["from"], object_ids)
            self.assertIn(rel["to"], object_ids)

    def test_negative_hold_classes_present(self):
        ids = {x["id"] for x in self.neg["classes"]}
        for required in [
            "cs.negative::no-go::v0.4",
            "cs.negative::contradiction::v0.4",
            "cs.negative::hold::v0.4",
            "cs.negative::bounded-search::v0.4",
        ]:
            self.assertIn(required, ids)

    def test_deep_skill_spindle(self):
        self.assertGreaterEqual(len(self.skills["skills"]), 12)
        for skill in self.skills["skills"]:
            self.assertTrue(skill["guards"])
            self.assertTrue(skill["method"])
            self.assertTrue(skill["required_capabilities"])

    def test_theorem_dependency_coverage(self):
        main = json.loads((ROOT / "registry" / "OMEGA_REGISTRY.json").read_text(encoding="utf-8"))
        expected = {x["id"] for x in main["theorematic_objects"]}
        actual = {x["theorem_id"] for x in self.deps["dependencies"]}
        self.assertEqual(actual, expected)

    def test_authority_delta_none(self):
        for doc in [self.objects, self.prov, self.rel, self.neg, self.skills, self.deps]:
            self.assertEqual(doc["authority_delta"], "NONE")

    def test_validator_passes(self):
        run = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "validate_objectization04.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["authority_delta"], "NONE")

if __name__ == "__main__":
    unittest.main()
