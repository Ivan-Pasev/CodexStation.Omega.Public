import json, unittest
from pathlib import Path
from tools.verify_private_receipt08f import verify

ROOT=Path(__file__).resolve().parents[1]

class Bridge08FTests(unittest.TestCase):
    def setUp(self):
        self.pins=json.loads((ROOT/"bridge08f/EXPECTED_PINS.json").read_text())
        self.sample=json.loads((ROOT/"bridge08f/SAMPLE_RECEIPT.json").read_text())

    def test_three_sources_pinned(self):
        self.assertEqual({x["source_family"] for x in self.pins["sources"]},{"DIGITAL_FABRICA_CORE","HIGHESTONE","NEURAL_LATTICE"})

    def test_sample_valid(self):
        self.assertEqual(verify(self.sample),[])

    def test_wrong_pin_rejected(self):
        bad=dict(self.sample); bad["source_commit"]="0"*40
        self.assertIn("source commit mismatch",verify(bad))

    def test_disclosure_rejected(self):
        bad=dict(self.sample); bad["private_source_disclosed"]=True
        self.assertIn("source disclosure forbidden",verify(bad))

    def test_mutation_rejected(self):
        bad=dict(self.sample); bad["source_tree_modified_for_test"]=True
        self.assertIn("source tree modification forbidden",verify(bad))

if __name__=="__main__":
    unittest.main()
