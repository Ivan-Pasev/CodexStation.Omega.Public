import json,unittest
from pathlib import Path
from cybernetic09j.ingestion import ingest_inbox,ingest_batch
from cybernetic09i.acquisition import make_request
from cybernetic09h.run_host_witness import build_witness
from cybernetic09f.distributor import host_profile_digest

ROOT=Path(__file__).resolve().parents[1]
LEDGER=json.loads((ROOT/"cybernetic09i/ACQUISITION_LEDGER.json").read_text())

def att(host,eid):
    return {"host_id":host,"host_profile_digest":host_profile_digest(host),"attestation_class":"HOST_BOUND_RUNTIME","runtime_channel":"test","execution_id":eid,"evidence_refs":["test://origin"]}

def env(host,eid):
    req=make_request(host)
    w=build_witness(host_id=host,attestation=att(host,eid),telemetry=[],candidates=[],adapter_version="test")
    return {"request_id":req["request_id"],"challenge_id":req["challenge_id"],"challenge_digest":req["challenge_digest"],"host_witness":w}

class Cybernetic09JTests(unittest.TestCase):
    def test_empty_inbox_holds(self):
        r=ingest_inbox(LEDGER,{"returns":[]})
        self.assertEqual(r["status"],"HOLD_NO_RETURNED_HOST_ENVELOPES")
        self.assertEqual(r["counts"]["accepted"],0)

    def test_one_host_closes_only_one_host(self):
        r=ingest_batch(LEDGER,[env("chatgpt-codex","e1")])
        self.assertEqual(r["counts"]["accepted"],1)
        self.assertEqual(r["ledger"]["hosts"]["chatgpt-codex"]["acquisition_state"],"LIVE_CONFORMANCE_PASS")
        self.assertEqual(r["ledger"]["hosts"]["gemini-notebook"]["acquisition_state"],"LIVE_RECEIPT_PENDING")
        self.assertFalse(r["ledger"]["live_multi_host_conformance_closed"])

    def test_invalid_return_does_not_mutate_host(self):
        bad=env("chatgpt-codex","e1"); bad["challenge_digest"]="0"*64
        r=ingest_batch(LEDGER,[bad])
        self.assertEqual(r["ledger"]["hosts"]["chatgpt-codex"],LEDGER["hosts"]["chatgpt-codex"])

    def test_duplicate_does_not_double_admit(self):
        e=env("chatgpt-codex","e1")
        r=ingest_batch(LEDGER,[e,e])
        self.assertEqual(r["counts"]["accepted"],1)
        self.assertEqual(r["counts"]["held"],1)

    def test_two_hosts_close_test_copy(self):
        r=ingest_batch(LEDGER,[env("chatgpt-codex","e1"),env("gemini-notebook","e2")])
        self.assertEqual(r["aggregate"]["status"],"LIVE_MULTI_HOST_CONFORMANCE_PASS")

if __name__=="__main__":
    unittest.main()
