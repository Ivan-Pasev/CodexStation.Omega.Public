import json, pathlib, subprocess, sys, tempfile, unittest, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
PREVIOUS="daa85b0bf47e392c4a310b2dc11f8074dee2480b5b7dd34c3bde917981bd4c7d"

class Packaging08ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chat=json.loads((ROOT/"packaging08a/chatgpt-plugin/PACKAGING.json").read_text())
        cls.gem=json.loads((ROOT/"packaging08a/gemini-notebook/PACKAGING.json").read_text())

    def test_previous_parent_same(self):
        for spec in [self.chat,self.gem]:
            self.assertEqual(spec["previous_composite_semantic_fingerprint"],PREVIOUS)
            self.assertEqual(spec["authority_delta"],"NONE")
            self.assertFalse(spec["release_eligible"])

    def test_profiles_distinct(self):
        self.assertNotEqual(self.chat["profile"],self.gem["profile"])
        self.assertNotEqual(self.chat["root_name"],self.gem["root_name"])

    def test_mount_skill_packaged(self):
        destinations={dst for _,dst in self.chat["package_sources"]}
        self.assertIn("skills/codexstation-omega-project-mount/SKILL.md",destinations)
        self.assertIn("skills/codexstation-omega-project-mount/references/KERNEL_LATTICE.json",destinations)

    def test_gemini_mount_sources(self):
        destinations={dst for _,dst in self.gem["package_sources"]}
        self.assertIn("MOUNT_PROTOCOL.md",destinations)
        self.assertIn("_machine/MOUNT_REGISTRY.json",destinations)
        self.assertIn("_machine/KERNEL_LATTICE.json",destinations)

    def test_reproducible_builder(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ra=subprocess.run([sys.executable,str(ROOT/"tools/build_packages08a.py"),"--out",a],capture_output=True,text=True)
            rb=subprocess.run([sys.executable,str(ROOT/"tools/build_packages08a.py"),"--out",b],capture_output=True,text=True)
            self.assertEqual(ra.returncode,0,ra.stdout+ra.stderr)
            self.assertEqual(rb.returncode,0,rb.stdout+rb.stderr)
            ja=json.loads(ra.stdout); jb=json.loads(rb.stdout)
            self.assertEqual(ja["result"],"PASS")
            self.assertEqual([x["sha256"] for x in ja["packages"]],[x["sha256"] for x in jb["packages"]])
            self.assertEqual(
                {x["composite_semantic_fingerprint"] for x in ja["packages"]},
                {x["composite_semantic_fingerprint"] for x in jb["packages"]}
            )
            for pkg in ja["packages"]:
                with zipfile.ZipFile(pkg["path"]) as zf:
                    self.assertTrue(any(x.endswith("/PACKAGE_MANIFEST.json") for x in zf.namelist()))

if __name__=="__main__":
    unittest.main()
