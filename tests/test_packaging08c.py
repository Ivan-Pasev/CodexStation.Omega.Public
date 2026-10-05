import json, pathlib, subprocess, sys, tempfile, unittest, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]

class Packaging08CTests(unittest.TestCase):
    def test_builds_two_deterministic_candidate_profiles(self):
        with tempfile.TemporaryDirectory() as td:
            run=subprocess.run([sys.executable,str(ROOT/"tools/build_packages08c.py"),"--out",td],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            report=json.loads(run.stdout)
            self.assertEqual(report["result"],"PASS")
            self.assertEqual(len(report["packages"]),2)
            self.assertEqual(len({p["composite_semantic_fingerprint"] for p in report["packages"]}),1)
            for p in report["packages"]:
                self.assertEqual(p["authority_delta"],"NONE")
                self.assertTrue(pathlib.Path(p["path"]).is_file())
                with zipfile.ZipFile(p["path"]) as zf:
                    self.assertTrue(any(n.endswith("/PACKAGE_MANIFEST.json") for n in zf.namelist()))

    def test_chatgpt_contains_reference_runtime_skill(self):
        spec=json.loads((ROOT/"packaging08c/chatgpt-plugin/PACKAGING.json").read_text())
        dests={dst for _,dst in spec["package_sources"]}
        self.assertIn("skills/codexstation-omega-reference-runtime/SKILL.md",dests)
        self.assertIn("skills/codexstation-omega-reference-runtime/scripts/runtime.py",dests)
        self.assertIn("skills/codexstation-omega-reference-runtime/scripts/adapters.py",dests)
        self.assertFalse(spec["release_eligible"])

    def test_gemini_primary_sources_are_not_machine_execution_claims(self):
        spec=json.loads((ROOT/"packaging08c/gemini-notebook/PACKAGING.json").read_text())
        self.assertIn("RUNTIME_CONTRACT.md",spec["notebook_source_recommendation"])
        self.assertNotIn("_runtime/runtime.py",spec["notebook_source_recommendation"])
        self.assertEqual(spec["live_conformance"],"OPEN")

if __name__=="__main__":
    unittest.main()
