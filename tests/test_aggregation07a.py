import json, pathlib, subprocess, sys, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class Aggregation07ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ext=json.loads((ROOT/"aggregation07a/SEMANTIC_EXTENSION.json").read_text())
        cls.schema=json.loads((ROOT/"aggregation07a/SCHEMA_BUNDLE.json").read_text())
        cls.atlas=json.loads((ROOT/"aggregation07a/INITIAL_PUBLIC_KERNEL_ATLAS.json").read_text())

    def test_four_core_schema_defs(self):
        defs=self.schema["$defs"]
        for name in ["ProjectHarvestCapsule","KernelRecord","Holotope","ArchetonicPlate"]:
            self.assertIn(name,defs)
            self.assertEqual(defs[name]["properties"]["authority_delta"]["const"],"NONE")

    def test_open_live_gates_preserved(self):
        gates=set(self.ext["parallel_open_gates"])
        self.assertIn("NB00_LIVE_CONFORMANCE_01",gates)
        self.assertIn("RGT-04_BUNDLED_FALLBACK_CLEAN_CHAT",gates)
        self.assertIn("LICENSE_IP_REVIEW",gates)

    def test_public_kernel_atlas(self):
        self.assertGreaterEqual(len(self.atlas["repositories"]),10)
        repos=[x["repo"] for x in self.atlas["repositories"]]
        self.assertEqual(len(repos),len(set(repos)))

    def test_authority_delta_none(self):
        self.assertEqual(self.ext["authority_delta"],"NONE")
        self.assertEqual(self.atlas["authority_delta"],"NONE")
        self.assertFalse(self.ext["release_eligible"])

    def test_validator_passes(self):
        run=subprocess.run([sys.executable,str(ROOT/"tools/validate_aggregation07a.py")],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        report=json.loads(run.stdout)
        self.assertEqual(report["result"],"PASS")
        self.assertEqual(report["authority_delta"],"NONE")

if __name__=="__main__":
    unittest.main()
