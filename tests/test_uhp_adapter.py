"""Adversarial, pure stdlib tests for proposed UHP integration; no network."""
import copy
import unittest
from runtime08c.uhp_adapter import (
    SCHEMA, UHPContractError, compile_task, normalize_response)

def work():
    return {"schema": SCHEMA, "work_order_id": "w:1", "project_id": "p:1",
            "input": "Read README and list headings. No changes.",
            "harness_id": "chrn:test", "model": "model:approved",
            "source_digest": "sha256:" + "a"*64, "effect_class": "READ_ONLY",
            "max_step": 3, "timeout_seconds": 60, "hard_tool_restrictions": False}

def caps():
    return {"version": "2026-10-19", "harness_ids": ["chrn:test"],
            "environments": True}

def resp():
    return {"id": "resp_test", "object": "response", "created_at": 1793860000,
            "status": "completed", "model": "model:approved",
            "store": False, "error": None, "incomplete_details": None,
            "previous_response_id": None, "usage": None,
            "metadata": {"harness_id": "chrn:test", "session_id": "hsess_test",
                         "ignored_fields": []}, "output": []}

class UHPAdapterTests(unittest.TestCase):
    def test_compilation_no_authority(self):
        req, c = compile_task(work(), caps())
        self.assertEqual(req["metadata"]["harness_id"], "chrn:test")
        self.assertNotIn("tools", req)
        self.assertNotIn("include", req)
        self.assertFalse(c["dispatch_authorized"])
        self.assertEqual(c["canonical_authority_delta"], "NONE")

    def test_reproducible(self):
        self.assertEqual(compile_task(work(), caps()), compile_task(work(), caps()))

    def test_completed_still_unverified(self):
        _, c = compile_task(work(), caps())
        o = normalize_response(c, resp())
        self.assertEqual(o["verdict"], "TASK_COMPLETED_EFFECT_UNVERIFIED")
        self.assertEqual(o["effect_confirmation"], "UNKNOWN_OUTCOME")
        self.assertFalse(o["promotion_authorized"])

    def test_environment_dialect(self):
        w = work()
        w["environment_id"] = "henv:test"
        req, c = compile_task(w, caps())
        self.assertEqual(req["metadata"]["environment"], "henv:test")
        self.assertNotIn("environment", req)
        r = resp()
        r["metadata"]["environment"] = "henv:test"
        self.assertEqual(normalize_response(c, r)["verdict"],
                         "TASK_COMPLETED_EFFECT_UNVERIFIED")

    def test_environment_without_capability(self):
        w = work()
        w["environment_id"] = "henv:test"
        cp = caps()
        cp["environments"] = False
        with self.assertRaises(UHPContractError): compile_task(w, cp)

    def test_effectful_rejected(self):
        for effect in ("WRITE", "DESTRUCTIVE", None):
            w = work()
            w["effect_class"] = effect
            with self.assertRaises(UHPContractError): compile_task(w, caps())

    def test_tool_restriction_rejected(self):
        for value in (True, None):
            w = work()
            w["hard_tool_restrictions"] = value
            with self.assertRaises(UHPContractError): compile_task(w, caps())

    def test_unknown_fields_rejected(self):
        for field in ("tools", "include", "authorization", "previous_response_id"):
            w = work()
            w[field] = []
            with self.assertRaises(UHPContractError): compile_task(w, caps())

    def test_version_mismatch(self):
        cp = caps()
        cp["version"] = "2026-09-12"
        with self.assertRaises(UHPContractError): compile_task(work(), cp)

    def test_unobserved_harness(self):
        cp = caps()
        cp["harness_ids"] = ["chrn:other"]
        with self.assertRaises(UHPContractError): compile_task(work(), cp)

    def test_invalid_source_digests(self):
        for value in ("sha256:x", "a"*64, "sha256:"+"G"*64):
            w = work()
            w["source_digest"] = value
            with self.assertRaises(UHPContractError): compile_task(w, caps())

    def test_budget_enforcement(self):
        for field, value in (("max_step", True), ("max_step", 9),
                             ("timeout_seconds", 301), ("timeout_seconds", 0)):
            w = work()
            w[field] = value
            with self.assertRaises(UHPContractError): compile_task(w, caps())

    def test_model_substitution_hold(self):
        _, c = compile_task(work(), caps())
        r = resp()
        r["model"] = "other"
        self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")
        r = resp()
        r["metadata"]["model_fallback"] = True
        self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")

    def test_harness_mismatch_hold(self):
        _, c = compile_task(work(), caps())
        r = resp()
        r["metadata"]["harness_id"] = "chrn:foreign"
        self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")

    def test_ignored_contract_budget_hold(self):
        _, c = compile_task(work(), caps())
        r = resp()
        r["metadata"]["ignored_fields"] = ["timeout_seconds"]
        self.assertEqual(normalize_response(c, r)["hold_reasons"],
                         ["IGNORED_CONTRACT_FIELD"])

    def test_nonterminal_and_terminal_do_not_promote(self):
        _, c = compile_task(work(), caps())
        for status in ("in_progress", "failed", "incomplete", "cancelled"):
            r = resp()
            r["status"] = status
            self.assertFalse(normalize_response(c, r)["promotion_authorized"])

    def test_unknown_status_fail_closed(self):
        _, c = compile_task(work(), caps())
        r = resp()
        r["status"] = "queued"
        with self.assertRaises(UHPContractError): normalize_response(c, r)

    def test_authorization_smuggling_rejected(self):
        _, c = compile_task(work(), caps())
        c["dispatch_authorized"] = True
        with self.assertRaises(UHPContractError): normalize_response(c, resp())

    def test_no_mutation(self):
        _, c = compile_task(work(), caps())
        r = resp()
        before = copy.deepcopy(r)
        normalize_response(c, r)
        self.assertEqual(r, before)


    def test_static_discovery_non_authorizing(self):
        from runtime08c.uhp_adapter import analyze_discovery
        discovery = {"object": "uhp.discovery", "protocol": "uhp",
                     "versions": ["2026-10-19"], "default_version": "2026-10-19",
                     "conformance_class": "core", "capabilities": {"sessions": True}}
        report = analyze_discovery(discovery)
        self.assertEqual(report["syntactic_compatibility"], "PASS")
        self.assertFalse(report["server_identity_attested"])
        self.assertFalse(report["dispatch_authorized"])

    def test_static_discovery_rejects_wrong_type_or_version(self):
        from runtime08c.uhp_adapter import analyze_discovery
        for changed in ({"object": "something-else"},
                        {"versions": ["2026-10-04"]},
                        {"capabilities": {"sessions": "true"}},
                        {"conformance_class": "extended"}):
            d = {"object": "uhp.discovery", "protocol": "uhp",
                 "versions": ["2026-10-19"], "default_version": "2026-10-19",
                 "conformance_class": "core", "capabilities": {"sessions": True}}
            d.update(changed)
            self.assertEqual(analyze_discovery(d)["syntactic_compatibility"], "HOLD")

    def test_response_envelope_must_have_required_fields(self):
        _, c = compile_task(work(), caps())
        cases = (("object", "not-response"), ("created_at", True),
                 ("output", None), ("usage", "0"), ("previous_response_id", []),
                 ("store", True))
        for key, value in cases:
            with self.subTest(key=key):
                r = resp()
                r[key] = value
                self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")

    def test_missing_response_fields_cannot_complete(self):
        _, c = compile_task(work(), caps())
        for field in ("object", "created_at", "output", "usage", "error",
                      "incomplete_details", "previous_response_id", "store"):
            with self.subTest(field=field):
                r = resp()
                del r[field]
                self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")

    def test_missing_session_id_holds(self):
        _, c = compile_task(work(), caps())
        r = resp()
        del r["metadata"]["session_id"]
        self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")

    def test_failed_and_incomplete_require_coherent_details(self):
        _, c = compile_task(work(), caps())
        failed = resp()
        failed["status"] = "failed"
        self.assertEqual(normalize_response(c, failed)["verdict"], "HOLD")
        failed["error"] = {"code": "test_error", "message": "synthetic"}
        self.assertEqual(normalize_response(c, failed)["verdict"], "FAILED_NO_PROMOTION")
        incomplete = resp()
        incomplete["status"] = "incomplete"
        self.assertEqual(normalize_response(c, incomplete)["verdict"], "HOLD")
        incomplete["incomplete_details"] = {"reason": "timeout"}
        self.assertEqual(normalize_response(c, incomplete)["verdict"],
                         "INCOMPLETE_NO_PROMOTION")

    def test_ignored_input_or_stream_holds(self):
        _, c = compile_task(work(), caps())
        for field in ("input", "stream"):
            r = resp()
            r["metadata"]["ignored_fields"] = [field]
            self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")

    def test_requested_model_metadata_mismatch_holds(self):
        _, c = compile_task(work(), caps())
        r = resp()
        r["metadata"]["requested_model"] = "different"
        self.assertIn("MODEL_SUBSTITUTION",
                      normalize_response(c, r)["hold_reasons"])

    def test_non_json_object_cannot_create_positive_observation(self):
        _, c = compile_task(work(), caps())
        r = resp()
        r["output"] = [set(["untrusted"])]
        self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")
        self.assertIsNone(normalize_response(c, r)["response_sha256"])

    def test_oversized_envelope_holds(self):
        _, c = compile_task(work(), caps())
        r = resp()
        r["output"] = ["z" * 270000]
        self.assertEqual(normalize_response(c, r)["verdict"], "HOLD")

    def test_read_only_label_is_not_technical_enforcement(self):
        _, c = compile_task(work(), caps())
        report = normalize_response(c, resp())
        self.assertEqual(report["read_only_enforcement"], "NOT_ATTESTED")
        self.assertFalse(report["source_content_verified"])
        self.assertFalse(report["server_identity_attested"])
        self.assertFalse(report["promotion_authorized"])

if __name__ == "__main__":
    unittest.main()
