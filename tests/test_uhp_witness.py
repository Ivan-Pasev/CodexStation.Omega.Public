"""Offline evidence witness contract: synthetic bytes, no real machine effects."""
import copy
import hashlib
import unittest

from runtime08c.uhp_adapter import (
    SCHEMA, UHPContractError, compile_task, normalize_response,
)
from runtime08c.uhp_preflight import compile_transport_preview
from runtime08c.uhp_witness import (
    snapshot_manifest, review_offline_evidence,
)

def source():
    return {"README.md": b"# Demonstration\n", "src/a.py": b"print(1)\n"}

def capabilities():
    return {"version": "2026-10-19", "harness_ids": ["chrn:synthetic"],
            "environments": False}

def discovery():
    return {"object": "uhp.discovery", "protocol": "uhp",
            "versions": ["2026-10-19"], "default_version": "2026-10-19",
            "conformance_class": "core",
            "capabilities": {"idempotency": True}}

def response():
    return {"id": "resp_synthetic", "object": "response", "created_at": 1793860000,
            "status": "completed", "model": "model-synthetic",
            "store": False, "error": None, "incomplete_details": None,
            "previous_response_id": None, "usage": None,
            "metadata": {"harness_id": "chrn:synthetic", "session_id": "hsess_synthetic",
                         "ignored_fields": []}, "output": []}

def fixture():
    before = source()
    order = {
        "schema": SCHEMA, "work_order_id": "witness-04", "project_id": "p04",
        "input": "Read the README headings. No source changes.",
        "harness_id": "chrn:synthetic", "model": "model-synthetic",
        "source_digest": snapshot_manifest(before)["digest"],
        "effect_class": "READ_ONLY", "max_step": 2,
        "timeout_seconds": 30, "hard_tool_restrictions": False,
    }
    req, contract = compile_task(order, capabilities())
    preview = compile_transport_preview(req, contract, discovery())
    observed = normalize_response(contract, response())
    return contract, preview, observed, before

def review(*, before=None, after=None, claims=None, artifacts=None,
           contract=None, preview=None, observed=None):
    c, p, o, b = fixture()
    b = b if before is None else before
    a = copy.deepcopy(b) if after is None else after
    return review_offline_evidence(
        c if contract is None else contract,
        p if preview is None else preview,
        o if observed is None else observed,
        b, a, [] if claims is None else claims,
        {} if artifacts is None else artifacts,
    )

class UHPWitnessTests(unittest.TestCase):
    def test_snapshot_order_invariance(self):
        a = snapshot_manifest(source())
        b = snapshot_manifest(dict(reversed(list(source().items()))))
        self.assertEqual(a, b)

    def test_snapshot_content_sensitive(self):
        a = source()
        b = copy.deepcopy(a)
        b["README.md"] = b"# Different\n"
        self.assertNotEqual(snapshot_manifest(a)["digest"], snapshot_manifest(b)["digest"])

    def test_snapshot_refuses_path_traversal_and_absolute(self):
        for path in ("../secret", "/etc/passwd", "a/../b", "a/./b",
                     "C:\\windows", "a%2Fb", "a//b", "ä.txt", ""):
            with self.subTest(path=path), self.assertRaises(UHPContractError):
                snapshot_manifest({path: b"x"})

    def test_snapshot_requires_exact_bytes(self):
        for v in ("a text string", bytearray(b"abc"), None):
            with self.subTest(value=str(v)), self.assertRaises(UHPContractError):
                snapshot_manifest({"file": v})

    def test_snapshot_size_and_count_bounds(self):
        with self.assertRaises(UHPContractError):
            snapshot_manifest({"a.txt": b"x" * 131073})
        with self.assertRaises(UHPContractError):
            snapshot_manifest({f"{n}.txt": b"x" for n in range(33)})

    def test_unchanged_is_only_consistent_not_attested(self):
        r = review()
        self.assertEqual(r["verdict"], "OFFLINE_CONSISTENT_UNATTESTED")
        self.assertFalse(r["observer_identity_attested"])
        self.assertFalse(r["source_capture_independence_attested"])
        self.assertFalse(r["external_effects_verified"])
        self.assertFalse(r["sandbox_enforcement_verified"])
        self.assertFalse(r["promotion_authorized"])
        self.assertEqual(r["effect_confirmation"], "UNKNOWN_OUTCOME")

    def test_mutated_source_detected(self):
        a = source()
        a["README.md"] = b"modified"
        r = review(after=a)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertEqual(r["source_changes"], ["README.md"])

    def test_added_source_detected(self):
        a = source()
        a["secret.txt"] = b"new"
        self.assertEqual(review(after=a)["verdict"], "HOLD")

    def test_deleted_source_detected(self):
        a = source()
        del a["src/a.py"]
        self.assertEqual(review(after=a)["verdict"], "HOLD")

    def test_artifact_byte_hash_matches_claim_but_never_promotes(self):
        b = b"generated report"
        digest = "sha256:" + hashlib.sha256(b).hexdigest()
        r = review(claims=[{"path": "reports/out.txt", "sha256": digest}],
                   artifacts={"reports/out.txt": b})
        self.assertEqual(r["verdict"], "OFFLINE_CONSISTENT_UNATTESTED")
        self.assertFalse(r["artifact_claims_authoritative"])

    def test_claim_without_bytes_holds(self):
        r = review(claims=[{"path": "reports/o.txt", "sha256": "sha256:" + "b"*64}])
        self.assertEqual(r["verdict"], "HOLD")
        self.assertEqual(r["missing_artifacts"], ["reports/o.txt"])

    def test_unclaimed_bytes_hold(self):
        r = review(artifacts={"reports/o.txt": b"unclaimed"})
        self.assertEqual(r["verdict"], "HOLD")
        self.assertEqual(r["unexpected_artifacts"], ["reports/o.txt"])

    def test_artifact_digest_mismatch_holds(self):
        r = review(claims=[{"path": "reports/o.txt", "sha256": "sha256:" + "0"*64}],
                   artifacts={"reports/o.txt": b"real"})
        self.assertEqual(r["verdict"], "HOLD")
        self.assertEqual(r["digest_mismatched_artifacts"], ["reports/o.txt"])

    def test_duplicate_claim_fails_closed(self):
        claim = {"path": "report.txt", "sha256": "sha256:" + "a"*64}
        with self.assertRaises(UHPContractError):
            review(claims=[claim, claim])

    def test_malformed_claim_fails_closed(self):
        with self.assertRaises(UHPContractError):
            review(claims=[{"path": "../x", "sha256": "sha256:"+"0"*64}])
        with self.assertRaises(UHPContractError):
            review(claims=[{"path": "x", "sha256": "wrong"}])

    def test_altered_source_binding_rejected(self):
        c, p, o, b = fixture()
        c["source_digest"] = "sha256:" + "e"*64
        with self.assertRaises(UHPContractError):
            review(contract=c)

    def test_altered_transport_binding_rejected(self):
        c, p, o, b = fixture()
        p["request_sha256"] = "f" * 64
        with self.assertRaises(UHPContractError):
            review(preview=p)

    def test_altered_work_order_binding_rejected(self):
        c, p, o, b = fixture()
        o["work_order_id"] = "witness-forged"
        with self.assertRaises(UHPContractError):
            review(observed=o)

    def test_forged_dispatch_authority_rejected(self):
        c, p, o, b = fixture()
        p["dispatch_authorized"] = True
        with self.assertRaises(UHPContractError):
            review(preview=p)

    def test_forged_promotion_rejected(self):
        c, p, o, b = fixture()
        o["promotion_authorized"] = True
        with self.assertRaises(UHPContractError):
            review(observed=o)

    def test_forged_external_gate_pass_rejected(self):
        c, p, o, b = fixture()
        p["external_gates"]["sandbox_isolation"] = "PASS"
        with self.assertRaises(UHPContractError):
            review(preview=p)

    def test_fake_attestation_rejected(self):
        c, p, o, b = fixture()
        o["server_identity_attested"] = True
        with self.assertRaises(UHPContractError):
            review(observed=o)

    def test_untrusted_model_self_report_does_not_verify_effect(self):
        c, p, o, b = fixture()
        o["verdict"] = "AGENT_SAYS_ALL_DONE"
        self.assertEqual(review(observed=o)["verdict"], "HOLD")

    def test_failed_or_incomplete_task_holds(self):
        for status in ("failed", "incomplete", "cancelled", "in_progress"):
            with self.subTest(status=status):
                c, p, o, b = fixture()
                o["uhp_status"] = status
                self.assertEqual(review(observed=o)["verdict"], "HOLD")

    def test_invalid_response_digest_rejected(self):
        c, p, o, b = fixture()
        o["response_sha256"] = "0"*3
        with self.assertRaises(UHPContractError):
            review(observed=o)

    def test_no_raw_artifact_text_leak_in_receipt(self):
        contents = b"do not emit this secret test value"
        digest = "sha256:" + hashlib.sha256(contents).hexdigest()
        r = review(claims=[{"path": "artifact.txt", "sha256": digest}],
                   artifacts={"artifact.txt": contents})
        self.assertNotIn("do not emit", str(r))

    def test_inputs_remain_unmodified(self):
        c, p, o, b = fixture()
        b0, c0, p0, o0 = (copy.deepcopy(v) for v in (b, c, p, o))
        review_offline_evidence(c, p, o, b, copy.deepcopy(b), [], {})
        self.assertEqual((b, c, p, o), (b0, c0, p0, o0))

    def test_empty_baseline_does_not_certify_source(self):
        c, p, o, b = fixture()
        with self.assertRaises(UHPContractError):
            review_offline_evidence(c, p, o, {}, {}, [], {})

    def test_receipt_is_deterministic(self):
        self.assertEqual(review(), review())


if __name__ == "__main__":
    unittest.main()
