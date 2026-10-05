import json, pathlib, subprocess, sys, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class MountLattice08ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads((ROOT/"aggregation08a/SCHEMA_EXTENSION.json").read_text())
        cls.mounts=json.loads((ROOT/"aggregation08a/MOUNT_REGISTRY.json").read_text())
        cls.lattice=json.loads((ROOT/"aggregation08a/KERNEL_LATTICE.json").read_text())
        cls.ext=json.loads((ROOT/"aggregation08a/SEMANTIC_EXTENSION.json").read_text())

    def test_schema_defs(self):
        defs=self.schema["$defs"]
        for name in ["ProjectMount","HarvestSession","KnowledgeQuantum","LatticeAdmission","FeedbackPacket","KernelLatticeEntry"]:
            self.assertIn(name,defs)
            self.assertEqual(defs[name]["properties"]["authority_delta"]["const"],"NONE")

    def test_mounts_unique(self):
        ids=[x["mount_id"] for x in self.mounts["mounts"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),8)

    def test_kernel_lattice(self):
        ids=[x["kernel_id"] for x in self.lattice["kernels"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),18)
        for item in self.lattice["kernels"]:
            self.assertEqual(item["authority_delta"],"NONE")
            self.assertEqual(len(item["evidence_vector"]),9)

    def test_semantic_kernel_set(self):
        self.assertEqual(set(self.ext["kernel_ids"]),{x["kernel_id"] for x in self.lattice["kernels"]})

    def test_open_gates_preserved(self):
        gates=set(self.ext["parallel_open_gates"])
        self.assertIn("NB00_LIVE_CONFORMANCE_01",gates)
        self.assertIn("RGT-04_BUNDLED_FALLBACK_CLEAN_CHAT",gates)
        self.assertIn("LICENSE_IP_REVIEW",gates)
        self.assertFalse(self.ext["release_eligible"])
        self.assertEqual(self.ext["authority_delta"],"NONE")

    def test_validator_passes(self):
        run=subprocess.run([sys.executable,str(ROOT/"tools/validate_mount_lattice08a.py")],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        report=json.loads(run.stdout)
        self.assertEqual(report["result"],"PASS")
        self.assertEqual(report["authority_delta"],"NONE")

if __name__=="__main__":
    unittest.main()
