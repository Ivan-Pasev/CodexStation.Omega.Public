import json, pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class PublicOmegaBootstrapTests(unittest.TestCase):
    def test_manifest_boundary(self):
        m=json.loads((ROOT/"MANIFEST.json").read_text())
        self.assertEqual(m["status"],"PUBLICATION_STAGING")
        self.assertFalse(m["release_eligible"])
        self.assertEqual(m["authority_delta"],"NONE")

    def test_logical_carriers_exist(self):
        m=json.loads((ROOT/"MANIFEST.json").read_text())
        for rel in m["logical_carriers"]:
            self.assertTrue((ROOT/rel).is_file(), rel)

    def test_noncollapse_canaries(self):
        corpus="\n".join(p.read_text(errors="replace") for p in (ROOT/"canon").glob("*.md"))
        for c in [
            "MODEL != REALITY",
            "SOURCE != AUTHORITY",
            "FORMAL_PROOF != EMPIRICAL_CONFIRMATION",
            "IMPLEMENTATION_PASS != SCIENTIFIC_PASS",
        ]:
            self.assertIn(c,corpus)

    def test_no_license_claim(self):
        m=json.loads((ROOT/"MANIFEST.json").read_text())
        self.assertEqual(m["license_policy"],"OPEN_DECISION")

if __name__=="__main__":
    unittest.main()
