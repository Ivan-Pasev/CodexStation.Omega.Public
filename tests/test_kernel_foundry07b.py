import json, pathlib, subprocess, sys, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"kernel-foundry07b"

class KernelFoundry07BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger=json.loads((BASE/"SOURCE_LEDGER.json").read_text())
        cls.kernels=json.loads((BASE/"KERNEL_REGISTRY.json").read_text())
        cls.abi=json.loads((BASE/"SOVEREIGN_RUNTIME_ABI.json").read_text())
        cls.matrix=json.loads((BASE/"COMPATIBILITY_MATRIX.json").read_text())
        cls.ext=json.loads((BASE/"SEMANTIC_EXTENSION.json").read_text())

    def test_k0_to_k13_complete(self):
        aliases={x["alias"] for x in self.kernels["kernels"]}
        self.assertEqual(aliases,{f"K{i}" for i in range(14)})

    def test_every_kernel_is_source_grounded(self):
        sources={x["id"] for x in self.ledger["sources"]}
        for k in self.kernels["kernels"]:
            self.assertTrue(k["source_refs"])
            self.assertTrue(set(k["source_refs"]).issubset(sources))

    def test_abi_records_are_adapter_first(self):
        self.assertEqual(len(self.abi["records"]),10)
        self.assertIn("Native source systems retain",self.abi["compatibility_rule"])
        for rec in self.abi["records"]:
            self.assertTrue(rec["adapters"])
            self.assertTrue(rec["laws"])

    def test_compatibility_classes_are_bounded(self):
        allowed={"DIRECT","ADAPTER","PARTIAL","NONE_OBSERVED"}
        axes=["identity","transition","authority","invariants","event_replay","witness_receipt","rollback","knowledge_admission","conflict","execution","projection","release"]
        for system in self.matrix["systems"]:
            for axis in axes:
                self.assertIn(system[axis],allowed)

    def test_no_authority_promotion(self):
        for doc in [self.ledger,self.kernels,self.abi,self.matrix,self.ext]:
            self.assertEqual(doc["authority_delta"],"NONE")
        self.assertFalse(self.ext["release_eligible"])

    def test_live_gates_preserved(self):
        gates=set(self.ext["parallel_open_gates"])
        self.assertIn("NB00_LIVE_CONFORMANCE_01",gates)
        self.assertIn("RGT-04_BUNDLED_FALLBACK_CLEAN_CHAT",gates)
        self.assertIn("LICENSE_IP_REVIEW",gates)

    def test_validator_passes(self):
        run=subprocess.run([sys.executable,str(ROOT/"tools/validate_kernel_foundry07b.py")],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        report=json.loads(run.stdout)
        self.assertEqual(report["result"],"PASS")
        self.assertEqual(report["kernels"],14)
        self.assertEqual(report["abi_records"],10)

if __name__=="__main__":
    unittest.main()
