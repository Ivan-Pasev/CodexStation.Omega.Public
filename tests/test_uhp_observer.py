"""Adversarial offline MAC tests; all signing keys are synthetic fixtures."""
import copy
import hashlib
import hmac
import unittest
from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_witness import review_offline_evidence
from runtime08c.uhp_observer import (
    CLAIM_SCHEMA, ENVELOPE_SCHEMA, DOMAIN, _wire,
    verify_observer_envelope,
)
from tests.test_uhp_witness import fixture


def anchor():
    return {
        "observer_id": "observer:test", "observer_principal_id": "principal:observer",
        "observer_host_id": "host:observer", "agent_principal_id": "principal:agent",
        "agent_host_id": "host:agent", "scope": "DISPOSABLE_READ_ONLY",
        "mac_key": b"synthetic_key_is_not_a_real_trust_root_123456",
    }


def state():
    return {"last_sequence": 0, "last_digest": "sha256:" + "0" * 64,
            "seen_nonces": []}


def evidence():
    c, t, o, before = fixture()
    return review_offline_evidence(c, t, o, before, copy.deepcopy(before), [], {})


def claim(r=None, a=None, s=None):
    r = evidence() if r is None else r
    a = anchor() if a is None else a
    s = state() if s is None else s
    return {
        "schema": CLAIM_SCHEMA,
        "observer_id": a["observer_id"],
        "observer_principal_id": a["observer_principal_id"],
        "observer_host_id": a["observer_host_id"],
        "agent_principal_id": a["agent_principal_id"],
        "agent_host_id": a["agent_host_id"],
        "scope": a["scope"],
        "project_id": r["project_id"], "work_order_id": r["work_order_id"],
        "source_digest": r["bound_source_digest"],
        "request_sha256": r["bound_request_sha256"],
        "response_sha256": r["bound_response_sha256"],
        "offline_receipt_digest": r["receipt_digest"],
        "before_digest": r["baseline_manifest_digest"],
        "after_digest": r["observed_manifest_digest"],
        "artifact_digest": r["artifact_manifest_digest"],
        "sequence": s["last_sequence"] + 1,
        "nonce": "nonce:first",
        "previous_attestation_digest": s["last_digest"],
        "capture_start_unix": 1793890000,
        "capture_end_unix": 1793890001,
        "effects_claim": "NO_EXTERNAL_EFFECTS_CLAIMED",
    }


def sign(p, a=None):
    a = anchor() if a is None else a
    return {"schema": ENVELOPE_SCHEMA, "alg": "HMAC-SHA256",
            "payload": p,
            "mac": hmac.new(a["mac_key"], DOMAIN + _wire(p),
                            hashlib.sha256).hexdigest()}


def verify(r=None, e=None, a=None, s=None):
    r = evidence() if r is None else r
    a = anchor() if a is None else a
    s = state() if s is None else s
    return verify_observer_envelope(r, sign(claim(r, a, s), a) if e is None else e, a, s)


class ObserverTrustTests(unittest.TestCase):
    def test_matching_mac_is_not_independent_attestation(self):
        v = verify()
        self.assertEqual(v["verdict"], "OFFLINE_MAC_CONSISTENT_UNATTESTED")
        self.assertTrue(v["mac_matches_supplied_key"])
        for key in ("observer_identity_independently_attested",
                    "observer_host_independently_attested", "key_custody_verified",
                    "clock_trusted", "durable_replay_committed",
                    "sandbox_enforcement_verified", "external_effects_verified",
                    "dispatch_authorized", "promotion_authorized"):
            self.assertFalse(v[key], key)

    def test_deterministic_results(self):
        self.assertEqual(verify(), verify())

    def test_changed_claim_without_resign_holds(self):
        e = sign(claim())
        e["payload"]["nonce"] = "nonce:tamper"
        self.assertIn("SUPPLIED_KEY_MAC_MISMATCH", verify(e=e)["reasons"])

    def test_cross_order_even_when_resigned_holds(self):
        p = claim()
        p["work_order_id"] = "other"
        self.assertIn("EVIDENCE_BINDING_MISMATCH", verify(e=sign(p))["reasons"])

    def test_rebinding_source_even_when_resigned_holds(self):
        p = claim()
        p["source_digest"] = "sha256:" + "a" * 64
        self.assertIn("EVIDENCE_BINDING_MISMATCH", verify(e=sign(p))["reasons"])

    def test_rebinding_artifact_even_when_resigned_holds(self):
        p = claim()
        p["artifact_digest"] = "sha256:" + "b" * 64
        self.assertIn("EVIDENCE_BINDING_MISMATCH", verify(e=sign(p))["reasons"])

    def test_wrong_observer_anchor_holds(self):
        p = claim()
        p["observer_host_id"] = "host:foreign"
        self.assertIn("ANCHOR_BINDING_MISMATCH", verify(e=sign(p))["reasons"])

    def test_wrong_key_holds(self):
        a = anchor()
        a["mac_key"] = b"b" * 32
        self.assertFalse(verify(e=sign(claim()), a=a)["mac_matches_supplied_key"])

    def test_anchor_same_principal_rejected(self):
        a = anchor()
        a["observer_principal_id"] = a["agent_principal_id"]
        with self.assertRaises(UHPContractError): verify(a=a)

    def test_anchor_same_host_rejected(self):
        a = anchor()
        a["observer_host_id"] = a["agent_host_id"]
        with self.assertRaises(UHPContractError): verify(a=a)

    def test_weak_key_rejected(self):
        a = anchor()
        a["mac_key"] = b"weak"
        with self.assertRaises(UHPContractError): verify(a=a)

    def test_string_key_rejected(self):
        a = anchor()
        a["mac_key"] = "notbytes"
        with self.assertRaises(UHPContractError):
            verify(a=a, e=sign(claim()))

    def test_extra_anchor_field_rejected(self):
        a = anchor()
        a["trust_override"] = True
        with self.assertRaises(UHPContractError): verify(a=a)

    def test_unqualified_scope_rejected(self):
        a = anchor()
        a["scope"] = "ALL"
        with self.assertRaises(UHPContractError): verify(a=a)

    def test_alg_downgrade_rejected(self):
        e = sign(claim())
        e["alg"] = "none"
        with self.assertRaises(UHPContractError): verify(e=e)

    def test_extra_envelope_field_rejected(self):
        e = sign(claim())
        e["allow"] = True
        with self.assertRaises(UHPContractError): verify(e=e)

    def test_extra_claim_field_rejected(self):
        e = sign(claim())
        e["payload"]["allow"] = True
        with self.assertRaises(UHPContractError): verify(e=e)

    def test_unsafe_nonce_rejected(self):
        p = claim()
        p["nonce"] = "invalid\nnonce"
        with self.assertRaises(UHPContractError): verify(e=sign(p))

    def test_sequence_gap_holds(self):
        p = claim()
        p["sequence"] = 5
        self.assertIn("SEQUENCE_GAP_OR_REPLAY", verify(e=sign(p))["reasons"])

    def test_nonce_replay_holds(self):
        s = state()
        s["seen_nonces"] = ["nonce:first"]
        p = claim(s=s)
        self.assertIn("NONCE_REPLAY", verify(e=sign(p), s=s)["reasons"])

    def test_previous_digest_not_bound_holds(self):
        p = claim()
        p["previous_attestation_digest"] = "sha256:" + "f" * 64
        self.assertIn("PREVIOUS_ATTESTATION_MISMATCH", verify(e=sign(p))["reasons"])

    def test_timestamp_reversal_rejected(self):
        p = claim()
        p["capture_end_unix"] = p["capture_start_unix"] - 1
        with self.assertRaises(UHPContractError): verify(e=sign(p))

    def test_time_window_unbounded_rejected(self):
        p = claim()
        p["capture_end_unix"] += 7200
        with self.assertRaises(UHPContractError): verify(e=sign(p))

    def test_boolean_sequence_rejected(self):
        p = claim()
        p["sequence"] = True
        with self.assertRaises(UHPContractError): verify(e=sign(p))

    def test_effectful_claim_rejected(self):
        p = claim()
        p["effects_claim"] = "WRITE_CONFIRMED"
        with self.assertRaises(UHPContractError): verify(e=sign(p))

    def test_forged_review_digest_rejected(self):
        r = evidence()
        r["receipt_digest"] = "sha256:" + "e" * 64
        with self.assertRaises(UHPContractError): verify(r=r)

    def test_forged_promotion_rejected(self):
        r = evidence()
        r["promotion_authorized"] = True
        with self.assertRaises(UHPContractError): verify(r=r)

    def test_offline_review_hold_stays_hold(self):
        r = evidence()
        r["verdict"] = "HOLD"
        r["receipt_digest"] = "sha256:" + hashlib.sha256(
            _wire({k: v for k,v in r.items() if k != "receipt_digest"})
        ).hexdigest()
        self.assertIn("OFFLINE_REVIEW_NOT_CONSISTENT",
                      verify(r=r, e=sign(claim(r)))["reasons"])

    def test_candidate_replay_is_not_committed(self):
        v = verify()
        self.assertEqual(v["candidate_replay_state"]["last_sequence"], 1)
        self.assertFalse(v["durable_replay_committed"])

    def test_second_claim_chains_but_not_committed(self):
        r = evidence()
        first = verify(r=r)
        s = first["candidate_replay_state"]
        p = claim(r=r, s=s)
        p["nonce"] = "nonce:second"
        v = verify(r=r, e=sign(p), s=s)
        self.assertEqual(v["verdict"], "OFFLINE_MAC_CONSISTENT_UNATTESTED")
        self.assertFalse(v["durable_replay_committed"])

    def test_bad_replay_state_rejected(self):
        s = state()
        s["seen_nonces"] = ["nonce:dup", "nonce:dup"]
        with self.assertRaises(UHPContractError): verify(s=s)

    def test_no_synthetic_key_in_output(self):
        r = repr(verify())
        self.assertNotIn(anchor()["mac_key"].decode("ascii"), r)
        self.assertNotIn("mac_key", r)

    def test_no_mutation(self):
        r, a, s = evidence(), anchor(), state()
        e = sign(claim(r, a, s), a)
        prev = copy.deepcopy((r, a, s, e))
        verify_observer_envelope(r, e, a, s)
        self.assertEqual((r, a, s, e), prev)


if __name__ == "__main__":
    unittest.main()
