import json, pathlib, subprocess, sys, tempfile, unittest, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE="eb43face6ab49b0eab112b5c9ddc6308a5dc0444c3d140622365c61976138719"
EXT="c74ce95fda667d384d95fc4852a932a2a5bdc242b0c819ab5012696988c9153a"
COMPOSITE="daa85b0bf47e392c4a310b2dc11f8074dee2480b5b7dd34c3bde917981bd4c7d"

class Packaging07ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chat=json.loads((ROOT/"packaging07a/chatgpt-plugin/PACKAGING.json").read_text())
        cls.gem=json.loads((ROOT/"packaging07a/gemini-notebook/PACKAGING.json").read_text())

    def test_shared_semantic_root(self):
        for spec in [self.chat,self.gem]:
            self.assertEqual(spec["base_semantic_parent_fingerprint"],BASE)
            self.assertEqual(spec["aggregation_extension_fingerprint"],EXT)
            self.assertEqual(spec["composite_semantic_fingerprint"],COMPOSITE)
            self.assertEqual(spec["authority_delta"],"NONE")
            self.assertFalse(spec["release_eligible"])

    def test_profiles_are_distinct(self):
        self.assertNotEqual(self.chat["profile"],self.gem["profile"])
        self.assertNotEqual(self.chat["root_name"],self.gem["root_name"])

    def test_harvester_is_packaged_for_chatgpt(self):
        destinations={dst for _,dst in self.chat["package_sources"]}
        self.assertIn("skills/codexstation-omega-harvester/SKILL.md",destinations)
        self.assertIn("skills/codexstation-omega-harvester/references/AGGREGATION_PROTOCOL.md",destinations)

    def test_gemini_has_dense_aggregation_source(self):
        destinations={dst for _,dst in self.gem["package_sources"]}
        self.assertIn("AGGREGATION_PROTOCOL.md",destinations)
        self.assertIn("_machine/SCHEMA_BUNDLE.json",destinations)

    def test_builder_reproducible(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ra=subprocess.run([sys.executable,str(ROOT/"tools/build_packages07a.py"),"--out",a],capture_output=True,text=True)
            rb=subprocess.run([sys.executable,str(ROOT/"tools/build_packages07a.py"),"--out",b],capture_output=True,text=True)
            self.assertEqual(ra.returncode,0,ra.stdout+ra.stderr)
            self.assertEqual(rb.returncode,0,rb.stdout+rb.stderr)
            ja=json.loads(ra.stdout); jb=json.loads(rb.stdout)
            self.assertEqual(ja["result"],"PASS")
            self.assertEqual([x["sha256"] for x in ja["packages"]],[x["sha256"] for x in jb["packages"]])
            for pkg in ja["packages"]:
                self.assertEqual(pkg["composite_semantic_fingerprint"],COMPOSITE)
                with zipfile.ZipFile(pkg["path"]) as zf:
                    self.assertTrue(any(x.endswith("/PACKAGE_MANIFEST.json") for x in zf.namelist()))

if __name__=="__main__":
    unittest.main()
