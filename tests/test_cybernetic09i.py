import copy,json,unittest
from pathlib import Path
from cybernetic09i.acquisition import make_request,verify_return,ingest_return,aggregate
from cybernetic09h.run_host_witness import build_witness
from cybernetic09f.distributor import host_profile_digest

ROOT=Path(__file__).resolve().parents[1]
LEDGER=json.loads((ROOT/"cybernetic09i/ACQUISITION_LEDGER.json").read_text())

def att(host,exec_id):
    return {
      "host_id":host,
      "host_profile_digest":host_profile_digest(host),
      "attestation_class":"HOST_BOUND_RUNTIME",
      "runtime_channel":"test-host-bound-channel",
      "execution_id":exec_id,
      "evidence_refs":["test://origin"]
    }

def returned(host,exec_id):
    req=make_request(host)
    w=build_witness(host_id=host,attestation=att(host,exec_id),telemetry=[],candidates=[],adapter_version="test")
    return req,{
      "request_id":req["request_id"],
      "challenge_id":req["challenge_id"],
      "challenge_digest":req["challenge_digest"],
      "host_witness":w
    }

class Cybernetic09ITests(unittest.TestCase):
    def test_initial_ledger_holds(self):
        self.assertEqual(aggregate(LEDGER)["status"],"HOLD_LIVE_RECEIPTS_PENDING")

    def test_matching_live_return_ingests_one_host(self):
        req,ret=returned("chatgpt-codex","exec-chat")
        out,v=ingest_return(LEDGER,req,ret)
        self.assertEqual(v["status"],"INGESTED")
        self.assertEqual(out["hosts"]["chatgpt-codex"]["acquisition_state"],"LIVE_CONFORMANCE_PASS")
        self.assertFalse(out["live_multi_host_conformance_closed"])

    def test_challenge_mismatch_holds(self):
        req,ret=returned("chatgpt-codex","exec-chat")
        ret["challenge_digest"]="0"*64
        self.assertEqual(verify_return(req,ret,LEDGER)["status"],"HOLD")

    def test_challenge_single_use(self):
        req,ret=returned("chatgpt-codex","exec-chat")
        out,_=ingest_return(LEDGER,req,ret)
        self.assertEqual(verify_return(req,ret,out)["status"],"HOLD")
        self.assertIn("CHALLENGE_ALREADY_CONSUMED",verify_return(req,ret,out)["reasons"])

    def test_two_hosts_close_only_in_test_copy(self):
        out=copy.deepcopy(LEDGER)
        for host,eid in [("chatgpt-codex","exec-chat"),("gemini-notebook","exec-gem")]:
            req,ret=returned(host,eid)
            out,v=ingest_return(out,req,ret)
            self.assertEqual(v["status"],"INGESTED")
        self.assertEqual(aggregate(out)["status"],"LIVE_MULTI_HOST_CONFORMANCE_PASS")
        self.assertFalse(LEDGER["live_multi_host_conformance_closed"])

    def test_reference_witness_cannot_ingest(self):
        req=make_request("chatgpt-codex")
        w=build_witness(host_id="chatgpt-codex",attestation=None,telemetry=[],candidates=[],adapter_version="test")
        ret={"request_id":req["request_id"],"challenge_id":req["challenge_id"],"challenge_digest":req["challenge_digest"],"host_witness":w}
        self.assertEqual(verify_return(req,ret,LEDGER)["status"],"HOLD")

if __name__=="__main__":
    unittest.main()
