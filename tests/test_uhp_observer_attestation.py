"""Slice 05 synthetic MAC tests; do not use test material in production."""
import copy
import hashlib
import hmac
import json
import unittest
from runtime08c.uhp_adapter import SCHEMA, UHPContractError, compile_task, normalize_response
from runtime08c.uhp_preflight import compile_transport_preview
from runtime08c.uhp_witness import review_offline_evidence, snapshot_manifest
from runtime08c.uhp_observer_attestation import (
    DOMAIN, ENVELOPE_SCHEMA, verify_detached_observer,
)

FAKE_KEY = bytes(range(32))
NOW = 1793890000
NONCE = "n" * 32


def review():
    files = {"README.md": b"# Synthetic\n", "src/p.py": b"print(1)\n"}
    order = {
        "schema": SCHEMA, "work_order_id": "w05", "project_id": "p05",
        "input": "Read headings only.", "harness_id": "chrn:test",
        "model": "model:test", "source_digest": snapshot_manifest(files)["digest"],
        "effect_class": "READ_ONLY", "max_step": 2,
        "timeout_seconds": 30, "hard_tool_restrictions": False,
    }
    req, contract = compile_task(order, {
        "version": "2026-10-19", "harness_ids": ["chrn:test"]})
    preview = compile_transport_preview(req, contract, {
        "object": "uhp.discovery", "protocol": "uhp",
        "versions": ["2026-10-19"], "default_version": "2026-10-19",
        "conformance_class": "core", "capabilities": {"idempotency": True},
    })
    response = {
        "id": "resp_test", "object": "response", "created_at": NOW,
        "status": "completed", "model": "model:test",
        "store": False, "error": None, "incomplete_details": None,
        "previous_response_id": None, "usage": None,
        "metadata": {"harness_id": "chrn:test", "session_id": "hsess_test",
                     "ignored_fields": []}, "output": [],
    }
    obs = normalize_response(contract, response)
    return review_offline_evidence(contract, preview, obs, files,
                                   copy.deepcopy(files), [], {})


def trust():
    return {
        "observer_id": "observer.test", "key_id": "test.key",
        "project_id": "p05", "purpose": "OFFLINE_CONSISTENCY",
        "status": "ACTIVE", "valid_from": NOW - 300, "valid_until": NOW + 300,
    }


def envelope(evidence):
    data = {
        "schema": ENVELOPE_SCHEMA, "observer_id": "observer.test",
        "key_id": "test.key", "project_id": evidence["project_id"],
        "work_order_id": evidence["work_order_id"],
        "receipt_digest": evidence["receipt_digest"],
        "source_digest": evidence["baseline_manifest_digest"],
        "after_digest": evidence["observed_manifest_digest"],
        "artifact_digest": evidence["artifact_manifest_digest"],
        "nonce": NONCE, "issued_at": NOW - 10, "expires_at": NOW + 120,
        "purpose": "OFFLINE_CONSISTENCY", "algorithm": "HMAC-SHA256",
    }
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("ascii")
    data["mac"] = hmac.new(FAKE_KEY, DOMAIN + raw, hashlib.sha256).hexdigest()
    return data


def check(*, evidence=None, sealed=None, record=None, key=FAKE_KEY,
          seen=frozenset(), time=NOW):
    e = review() if evidence is None else evidence
    return verify_detached_observer(e, envelope(e) if sealed is None else sealed,
                                     trust() if record is None else record,
                                     key, seen, time)


class DetachedObserverTests(unittest.TestCase):
    def test_valid_mac_not_observer_proof(self):
        r = check()
        self.assertEqual(r["verdict"], "MAC_MATCH_CUSTODY_UNVERIFIED")
        self.assertTrue(r["mac_matched_supplied_key"])
        self.assertFalse(r["independent_observer_attested"])
        self.assertFalse(r["observer_key_custody_attested"])
        self.assertFalse(r["source_capture_independence_attested"])
        self.assertFalse(r["external_effects_verified"])
        self.assertFalse(r["promotion_authorized"])

    def test_wrong_key_is_hold(self):
        r = check(key=b"q" * 32)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertIn("AUTHENTICATOR_MISMATCH", r["reasons"])

    def test_modified_nonce_detected_by_mac(self):
        e = review()
        sealed = envelope(e)
        sealed["nonce"] = "z" * 32
        self.assertEqual(check(evidence=e, sealed=sealed)["verdict"], "HOLD")

    def test_modification_of_mac_is_hold(self):
        e = review()
        sealed = envelope(e)
        sealed["mac"] = "f" * 64
        self.assertEqual(check(evidence=e, sealed=sealed)["verdict"], "HOLD")

    def test_scope_mismatch(self):
        for f in ("observer_id", "key_id", "project_id"):
            e = review()
            sealed = envelope(e)
            sealed[f] = "other"
            with self.subTest(f=f), self.assertRaises(UHPContractError):
                check(evidence=e, sealed=sealed)

    def test_work_order_mismatch(self):
        e = review()
        sealed = envelope(e)
        sealed["work_order_id"] = "other"
        with self.assertRaises(UHPContractError):
            check(evidence=e, sealed=sealed)

    def test_hash_binding_mismatch(self):
        for f in ("receipt_digest", "source_digest", "after_digest", "artifact_digest"):
            e = review()
            sealed = envelope(e)
            sealed[f] = "sha256:" + "0" * 64
            with self.subTest(f=f), self.assertRaises(UHPContractError):
                check(evidence=e, sealed=sealed)

    def test_tampered_review_rejected(self):
        e = review()
        e["source_changes"] = ["forged.txt"]
        with self.assertRaises(UHPContractError):
            check(evidence=e)

    def test_review_saying_hold_cannot_be_signed_into_success(self):
        e = review()
        e["verdict"] = "HOLD"
        with self.assertRaises(UHPContractError):
            check(evidence=e)

    def test_review_forged_promotion_rejected(self):
        for name in ("dispatch_authorized", "promotion_authorized",
                     "external_effects_verified", "observer_identity_attested"):
            e = review()
            e[name] = True
            with self.subTest(name=name), self.assertRaises(UHPContractError):
                check(evidence=e)

    def test_inactive_trust_record_holds(self):
        t = trust()
        t["status"] = "REVOKED"
        self.assertIn("INACTIVE_TRUST_RECORD", check(record=t)["reasons"])

    def test_expired_envelope_holds(self):
        r = check(time=NOW + 140)
        self.assertIn("ENVELOPE_WINDOW_FAILURE", r["reasons"])

    def test_future_envelope_holds(self):
        r = check(time=NOW - 100)
        self.assertIn("ENVELOPE_WINDOW_FAILURE", r["reasons"])

    def test_expired_trust_record_holds(self):
        t = trust()
        t["valid_until"] = NOW - 1
        self.assertEqual(check(record=t)["verdict"], "HOLD")

    def test_replayed_nonce_holds(self):
        r = check(seen=frozenset({NONCE}))
        self.assertIn("NONCE_PRESENT_IN_SUPPLIED_SNAPSHOT", r["reasons"])

    def test_nonce_set_does_not_certify_durable_ledger(self):
        self.assertFalse(check()["durable_replay_attested"])

    def test_wrong_key_length(self):
        with self.assertRaises(UHPContractError):
            check(key=b"x")

    def test_nonbyte_key(self):
        with self.assertRaises(UHPContractError):
            check(key="text")

    def test_mutable_replay_collection_rejected(self):
        with self.assertRaises(UHPContractError):
            check(seen=set())

    def test_invalid_nonce_rejected(self):
        e = review()
        sealed = envelope(e)
        sealed["nonce"] = "../bad"
        with self.assertRaises(UHPContractError):
            check(evidence=e, sealed=sealed)

    def test_algorithm_mismatch_rejected(self):
        e = review()
        sealed = envelope(e)
        sealed["algorithm"] = "none"
        with self.assertRaises(UHPContractError):
            check(evidence=e, sealed=sealed)

    def test_unauthorized_new_field_rejected(self):
        e = review()
        sealed = envelope(e)
        sealed["effect_pass"] = True
        with self.assertRaises(UHPContractError):
            check(evidence=e, sealed=sealed)

    def test_untrusted_trust_extension_rejected(self):
        t = trust()
        t["admin_acceptance"] = True
        with self.assertRaises(UHPContractError):
            check(record=t)

    def test_window_over_300_seconds_rejected(self):
        e = review()
        sealed = envelope(e)
        sealed["expires_at"] = sealed["issued_at"] + 301
        with self.assertRaises(UHPContractError):
            check(evidence=e, sealed=sealed)

    def test_boolean_time_rejected(self):
        e = review()
        sealed = envelope(e)
        sealed["issued_at"] = True
        with self.assertRaises(UHPContractError):
            check(evidence=e, sealed=sealed)

    def test_no_raw_source_or_key_in_result(self):
        r = check()
        self.assertNotIn("print(1)", str(r))
        self.assertNotIn("mac", list(r.keys()))
        self.assertNotIn(str(FAKE_KEY), str(r))

    def test_deterministic(self):
        self.assertEqual(check(), check())

    def test_malformed_mac_rejected(self):
        e = review()
        sealed = envelope(e)
        sealed["mac"] = "g" * 64
        with self.assertRaises(UHPContractError):
            check(evidence=e, sealed=sealed)
