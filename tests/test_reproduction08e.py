import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Reproduction08ETests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads((ROOT/"reproduction08e/REPRODUCTION_PROFILE.json").read_text())
        self.ledger = json.loads((ROOT/"reproduction08e/REPRODUCTION_LEDGER.json").read_text())
        self.by_family = {x["source_family"]:x for x in self.ledger["sources"]}

    def test_five_source_families_remain_distinct(self):
        self.assertEqual(len(self.ledger["sources"]), 5)
        self.assertEqual(set(self.by_family), {
            "DIGITAL_FABRICA_CORE","DFPL_PRIMA","HIGHESTONE","GILC_CODEXSTATION","NEURAL_LATTICE"
        })

    def test_private_sources_are_not_claimed_independently_reproduced(self):
        for family in ("DIGITAL_FABRICA_CORE","HIGHESTONE","NEURAL_LATTICE"):
            self.assertEqual(self.by_family[family]["visibility"], "private")
            self.assertEqual(self.by_family[family]["independent_reproduction"], "HOLD")

    def test_highestone_lineage_is_not_new_execution(self):
        h = self.by_family["HIGHESTONE"]
        self.assertFalse(h["lineage_check"]["relevant_formal_tree_changed"])
        self.assertEqual(h["status"], "SOURCE_NATIVE_LINEAGE_APPLICABLE_CI_ONLY")

    def test_dfpl_scope_is_partial(self):
        d = self.by_family["DFPL_PRIMA"]
        self.assertIn("Encoder B", d["semantic_scope"])
        self.assertIn("PRIMA", d["residual"])

    def test_gilc_exact_source_ci_exists(self):
        g = self.by_family["GILC_CODEXSTATION"]
        self.assertEqual(g["exact_commit_source_ci"]["run_id"], 33919239363)
        self.assertEqual(set(g["exact_commit_source_ci"]["python"].values()), {"success"})

    def test_neural_exact_source_ci_is_preserved(self):
        n = self.by_family["NEURAL_LATTICE"]
        self.assertEqual(n["exact_commit_source_ci"]["run_id"], 33970167198)
        self.assertEqual(n["exact_commit_source_ci"]["conclusion"], "success")

    def test_authority_boundary(self):
        self.assertEqual(self.profile["authority_delta"], "NONE")
        self.assertFalse(self.profile["release_eligible"])
        self.assertFalse(self.ledger["release_eligible"])

if __name__ == "__main__":
    unittest.main()
