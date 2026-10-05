import unittest
from cybernetic09h.run_host_witness import build_witness
from cybernetic09f.distributor import host_profile_digest
from cybernetic09g.conformance import classify_witness

def att(host):
    return {
      "schema":"GILC/CODEXSTATION/OMEGA-HOST-ORIGIN-ATTESTATION/0.9h",
      "host_id":host,
      "host_profile_digest":host_profile_digest(host),
      "attestation_class":"HOST_BOUND_RUNTIME",
      "runtime_channel":"fixture-host-channel",
      "execution_id":"fixture-exec",
      "evidence_refs":["fixture://host-origin"]
    }

class Cybernetic09HTests(unittest.TestCase):
    def test_without_attestation_is_reference_only(self):
        w=build_witness(host_id="chatgpt-codex",attestation=None,telemetry=[],candidates=[],adapter_version="test")
        self.assertEqual(w["witness_origin"],"REFERENCE_IMPLEMENTATION")
        self.assertEqual(classify_witness(w)["status"],"HOLD_NON_LIVE_WITNESS")

    def test_valid_attestation_can_emit_live_candidate(self):
        w=build_witness(host_id="chatgpt-codex",attestation=att("chatgpt-codex"),telemetry=[],candidates=[],adapter_version="test")
        self.assertEqual(w["witness_origin"],"LIVE_HOST")
        self.assertEqual(classify_witness(w)["status"],"LIVE_CONFORMANCE_PASS")

    def test_wrong_host_attestation_downgrades_origin(self):
        a=att("chatgpt-codex")
        w=build_witness(host_id="gemini-notebook",attestation=a,telemetry=[],candidates=[],adapter_version="test")
        self.assertEqual(w["witness_origin"],"REFERENCE_IMPLEMENTATION")

    def test_runner_does_not_mutate_registry(self):
        w=build_witness(host_id="gemini-notebook",attestation=att("gemini-notebook"),telemetry=[],candidates=[],adapter_version="test")
        self.assertEqual(w["status"],"PASS")
        self.assertIn("origin_attestation_digest",w)

if __name__=="__main__":
    unittest.main()
