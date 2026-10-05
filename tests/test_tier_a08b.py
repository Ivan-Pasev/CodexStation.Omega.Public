import json, pathlib, subprocess, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(rel): return json.loads((ROOT/rel).read_text())
class TierA08BTests(unittest.TestCase):
    def test_five_pinned_bindings(self):
        s=load("aggregation08b/SOURCE_BINDINGS.json")
        self.assertEqual(len(s["bindings"]),5)
        self.assertTrue(all(len(x["commit"])==40 for x in s["bindings"]))
    def test_abi_core(self):
        a=load("aggregation08b/CONSTITUTIONAL_ABI.json")
        self.assertIn("CanonicalState",a["primitives"])
        self.assertIn("CandidateTransition",a["primitives"])
        self.assertIn("Receipt",a["primitives"])
        self.assertEqual(a["authority_delta"],"NONE")
    def test_adapter_coverage(self):
        s={x["binding_id"] for x in load("aggregation08b/SOURCE_BINDINGS.json")["bindings"]}
        a={x["source_binding"] for x in load("aggregation08b/ADAPTER_MAP.json")["adapters"]}
        self.assertEqual(s,a)
    def test_open_gates_preserved(self):
        e=load("aggregation08b/SEMANTIC_EXTENSION.json")
        self.assertFalse(e["release_eligible"])
        self.assertIn("LICENSE_IP_REVIEW",e["parallel_open_gates"])
    def test_validator(self):
        p=subprocess.run([sys.executable,str(ROOT/"tools/validate_tier_a08b.py")],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)["result"],"PASS")
if __name__=="__main__": unittest.main()
