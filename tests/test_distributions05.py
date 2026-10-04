import json, pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class Distribution05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=json.loads((ROOT/"distribution05/SEMANTIC_PARENT.json").read_text())
        cls.compiled=json.loads((ROOT/"distribution05/COMPILED_SEMANTICS.json").read_text())
        cls.chat=json.loads((ROOT/"dist/chatgpt-codex/DISTRIBUTION.json").read_text())
        cls.gem=json.loads((ROOT/"dist/gemini-notebook/DISTRIBUTION.json").read_text())

    def test_same_parent(self):
        self.assertEqual(self.chat["semantic_parent_fingerprint"],self.gem["semantic_parent_fingerprint"])
        self.assertEqual(self.chat["semantic_parent_fingerprint"],self.parent["semantic_parent_fingerprint"])

    def test_same_sets(self):
        for key in self.chat["semantic_sets"]:
            self.assertEqual(set(self.chat["semantic_sets"][key]),set(self.gem["semantic_sets"][key]))

    def test_distinct_profiles(self):
        self.assertNotEqual(self.chat["provider_profile"],self.gem["provider_profile"])

    def test_no_release_promotion(self):
        self.assertFalse(self.chat["release_eligible"])
        self.assertFalse(self.gem["release_eligible"])
        self.assertEqual(self.chat["authority_delta"],"NONE")
        self.assertEqual(self.gem["authority_delta"],"NONE")

    def test_counts(self):
        for key,count in self.compiled["counts"].items():
            self.assertEqual(len(self.chat["semantic_sets"][key]),count)
            self.assertEqual(len(self.gem["semantic_sets"][key]),count)

    def test_chatgpt_canaries(self):
        text=(ROOT/"dist/chatgpt-codex/PUBLIC_OMEGA_CHATGPT_CODEX.md").read_text()
        self.assertIn("PLUGIN_SKILL != HOST_CAPABILITY",text)
        self.assertIn("PLATFORM_PROFILE != CANON_FORK",text)

    def test_gemini_canaries(self):
        text=(ROOT/"dist/gemini-notebook/PUBLIC_OMEGA_GEMINI_NOTEBOOK.md").read_text()
        self.assertIn("NOTEBOOK != STATION",text)
        self.assertIn("PLATFORM_PROFILE != CANON_FORK",text)

if __name__=="__main__":
    unittest.main()
