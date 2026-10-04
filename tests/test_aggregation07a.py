import json, pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"registry"/"aggregation07a"

class Aggregation07ATests(unittest.TestCase):
    def load(self,name):
        return json.loads((BASE/name).read_text(encoding="utf-8"))

    def test_capsule(self):
        d=self.load("FAB_SYS_PROJECT_HARVEST_CAPSULE.json")
        self.assertEqual(d["authority_delta"],"NONE")
        self.assertTrue(d["source_roots"])
        self.assertTrue(d["open_gates"])

    def test_holotope_plate_binding(self):
        h=self.load("HOLOTOPE_SOVEREIGN_DIGITAL_RUNTIME_CORE.json")
        p=self.load("PLATE_CODEXSTATION_EXECUTION_KNOWLEDGE_FABRIC.json")
        self.assertTrue(set(p["selected_methods_kernels"]).issubset(set(h["kernels"])))

    def test_kernel_registry(self):
        d=self.load("KERNEL_REGISTRY_SEED.json")
        ids=[x["id"] for x in d["kernels"]]
        self.assertGreaterEqual(len(ids),8)
        self.assertEqual(len(ids),len(set(ids)))
        for k in d["kernels"]:
            self.assertTrue(k["status"].startswith("SOURCE_BOUND"))

if __name__=="__main__":
    unittest.main()
