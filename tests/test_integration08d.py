import json
import unittest
from pathlib import Path

from integration08d.harness import run_all

ROOT = Path(__file__).resolve().parents[1]


class Integration08DTests(unittest.TestCase):
    def setUp(self):
        self.report = run_all()
        self.by_family = {x["source_family"]: x for x in self.report["results"]}

    def test_all_five_families_execute(self):
        self.assertEqual(self.report["result"], "PASS")
        self.assertEqual(self.report["source_families"], 5)
        self.assertEqual(set(self.by_family), {
            "DIGITAL_FABRICA_CORE","DFPL_PRIMA","HIGHESTONE","GILC_CODEXSTATION","NEURAL_LATTICE"
        })

    def test_residuals_are_not_erased(self):
        for result in self.report["results"]:
            self.assertTrue(result["residuals"])
            self.assertEqual(result["status"], "PASS_WITH_RESIDUALS")

    def test_digital_fabrica_stale_parent_fail_closed(self):
        self.assertEqual(self.by_family["DIGITAL_FABRICA_CORE"]["observations"]["stale_parent_status"], "HOLD")

    def test_dfpl_exact_plan_binding(self):
        obs = self.by_family["DFPL_PRIMA"]["observations"]
        self.assertTrue(obs["exact_plan_binding_enforced"])
        self.assertEqual(obs["tampered_plan_status"], "HOLD")

    def test_highestone_predecessor_and_recovery(self):
        obs = self.by_family["HIGHESTONE"]["observations"]
        self.assertEqual(obs["recovery"], "RECOVERABLE")
        self.assertEqual(obs["successor_authority_bootstrap"], "HOLD")

    def test_gilc_effect_unknown_is_preserved(self):
        obs = self.by_family["GILC_CODEXSTATION"]["observations"]
        self.assertEqual(obs["runtime_status_without_executor"], "UNKNOWN_OUTCOME")
        self.assertFalse(obs["successor_created"])

    def test_neural_lattice_conflict_is_durable(self):
        obs = self.by_family["NEURAL_LATTICE"]["observations"]
        self.assertTrue(obs["conflict_durable"])
        self.assertEqual(obs["conflict_status"], "UNRESOLVED")

    def test_fixture_commits_match_pinned_source_bindings(self):
        fixtures = json.loads((ROOT/"integration08d/SOURCE_FIXTURES.json").read_text())["fixtures"]
        bindings = json.loads((ROOT/"aggregation08b/SOURCE_BINDINGS.json").read_text())["bindings"]
        commits = {b["repository"]: b["commit"] for b in bindings}
        for f in fixtures:
            self.assertEqual(f["commit"], commits[f["repository"]])

    def test_authority_and_release_boundaries(self):
        profile = json.loads((ROOT/"integration08d/HARNESS_PROFILE.json").read_text())
        self.assertEqual(profile["authority_delta"], "NONE")
        self.assertFalse(profile["release_eligible"])
        self.assertFalse(self.report["release_eligible"])


if __name__ == "__main__":
    unittest.main()
