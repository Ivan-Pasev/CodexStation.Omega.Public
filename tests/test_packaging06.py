import json, pathlib, subprocess, sys, tempfile, unittest, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]

class Packaging06Tests(unittest.TestCase):
    def test_packager_builds_both_archives(self):
        with tempfile.TemporaryDirectory() as td:
            run=subprocess.run(
                [sys.executable,str(ROOT/"tools"/"build_packages06.py"),"--out",td],
                capture_output=True,text=True
            )
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            report=json.loads(run.stdout)
            self.assertEqual(report["result"],"PASS")
            self.assertEqual(len(report["packages"]),2)
            for pkg in report["packages"]:
                self.assertEqual(pkg["authority_delta"],"NONE")
                self.assertEqual(pkg["semantic_parent_fingerprint"],"eb43face6ab49b0eab112b5c9ddc6308a5dc0444c3d140622365c61976138719")
                self.assertEqual(pkg["parity_fingerprint"],"7ebb3332e2596fc53a2f956bbe26bf558fa96a93c159d0190625d10993d3dcd1")
                self.assertTrue(pathlib.Path(pkg["path"]).is_file())
                with zipfile.ZipFile(pkg["path"]) as zf:
                    names=zf.namelist()
                    self.assertTrue(any(n.endswith("/PACKAGE_MANIFEST.json") for n in names))

    def test_chatgpt_package_contract(self):
        spec=json.loads((ROOT/"packaging06/chatgpt-plugin/PACKAGING.json").read_text())
        self.assertEqual(spec["profile"],"CHATGPT_PLUGIN")
        self.assertFalse(spec["release_eligible"])
        self.assertEqual(spec["live_conformance"],"OPEN")
        destinations={dst for _,dst in spec["package_sources"]}
        self.assertIn("plugin.json",destinations)
        self.assertIn(".codex-plugin/plugin.json",destinations)
        self.assertIn("skills/codexstation-omega-public-orchestrator/SKILL.md",destinations)

    def test_gemini_package_contract(self):
        spec=json.loads((ROOT/"packaging06/gemini-notebook/PACKAGING.json").read_text())
        self.assertEqual(spec["profile"],"GEMINI_NOTEBOOK")
        self.assertFalse(spec["release_eligible"])
        self.assertEqual(spec["live_conformance"],"OPEN")
        recommended=set(spec["notebook_source_recommendation"])
        self.assertIn("OMEGA_CORE.md",recommended)
        self.assertIn("OMEGA_CRYSTAL.md",recommended)
        self.assertIn("OMEGA_SKILL_SPINDLE.md",recommended)

if __name__=="__main__":
    unittest.main()
