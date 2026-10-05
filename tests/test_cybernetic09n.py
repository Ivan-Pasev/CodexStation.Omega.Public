import copy, unittest
from cybernetic09n.dedup import audit, declarations

class Cybernetic09NTests(unittest.TestCase):
    def test_real_corpus_passes(self):
        r=audit()
        self.assertEqual(r["status"],"PASS",r["errors"])
        self.assertGreater(r["record_count"],0)

    def test_duplicate_id_fails(self):
        rows=declarations()[:2]
        b=copy.deepcopy(rows[0]); b["path"]="synthetic"; rows.append(b)
        r=audit(rows)
        self.assertEqual(r["status"],"FAIL")
        self.assertTrue(any(e["code"]=="DUPLICATE_CANONICAL_ID" for e in r["errors"]))

    def test_same_payload_different_id_fails(self):
        rows=declarations()[:1]
        b=copy.deepcopy(rows[0]); b["canonical_id"]="synthetic::other"; b["path"]="synthetic"; rows.append(b)
        r=audit(rows)
        self.assertEqual(r["status"],"FAIL")
        self.assertTrue(any(e["code"]=="IDENTICAL_PAYLOAD_DIFFERENT_IDS" for e in r["errors"]))

if __name__=="__main__":
    unittest.main()
