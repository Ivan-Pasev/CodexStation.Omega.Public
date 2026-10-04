import json, pathlib, subprocess, sys, tempfile, unittest, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]

class Packaging07ATests(unittest.TestCase):
    def test_build(self):
        with tempfile.TemporaryDirectory() as td:
            p=subprocess.run([sys.executable,str(ROOT/"tools"/"build_packages07a.py"),"--out",td],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            r=json.loads(p.stdout)
            self.assertEqual(r["result"],"PASS")
            self.assertEqual(len(r["packages"]),2)
            for pkg in r["packages"]:
                self.assertEqual(pkg["authority_delta"],"NONE")
                self.assertTrue(pathlib.Path(pkg["path"]).is_file())
                with zipfile.ZipFile(pkg["path"]) as z:
                    self.assertTrue(any(x.endswith("/PACKAGE_MANIFEST.json") for x in z.namelist()))

    def test_aggregation_sources_present(self):
        for rel in [
            "registry/aggregation07a/OMEGA_AGGREGATION_SCHEMA_BUNDLE.json",
            "registry/aggregation07a/FAB_SYS_PROJECT_HARVEST_CAPSULE.json",
            "registry/aggregation07a/KERNEL_REGISTRY_SEED.json",
            "registry/aggregation07a/HOLOTOPE_SOVEREIGN_DIGITAL_RUNTIME_CORE.json",
            "registry/aggregation07a/PLATE_CODEXSTATION_EXECUTION_KNOWLEDGE_FABRIC.json"
        ]:
            self.assertTrue((ROOT/rel).is_file())

if __name__=="__main__":
    unittest.main()
