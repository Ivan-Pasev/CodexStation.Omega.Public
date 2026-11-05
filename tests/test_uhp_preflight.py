"""Slice 03: all tests are pure, offline and non-dispatching."""
import copy
import unittest

from runtime08c.uhp_adapter import SCHEMA, UHPContractError, compile_task
from runtime08c.uhp_preflight import compile_transport_preview, assess_retry


def order():
    return {
        "schema": SCHEMA, "work_order_id": "work-03", "project_id": "p03",
        "input": "Read README.md headings only",
        "harness_id": "chrn:synthetic", "model": "model-approved",
        "source_digest": "sha256:" + "a" * 64, "effect_class": "READ_ONLY",
        "max_step": 2, "timeout_seconds": 30, "hard_tool_restrictions": False,
    }


def capabilities():
    return {
        "version": "2026-10-19",
        "harness_ids": ["chrn:synthetic"],
        "environments": True,
    }


def discovery():
    return {
        "object": "uhp.discovery", "protocol": "uhp",
        "versions": ["2026-10-19"], "default_version": "2026-10-19",
        "conformance_class": "core",
        "capabilities": {"idempotency": True, "sessions": True},
    }


def plan():
    req, contract = compile_task(order(), capabilities())
    return compile_transport_preview(req, contract, discovery())


class UHPTransportPreflightTests(unittest.TestCase):
    def test_valid_shape_is_not_dispatch_permission(self):
        p = plan()
        self.assertEqual(p["static_verdict"], "SHAPE_PASS_EXTERNAL_GATES_HOLD")
        self.assertFalse(p["dispatch_authorized"])
        self.assertFalse(p["retry_authorized"])
        self.assertEqual(p["canonical_authority_delta"], "NONE")

    def test_preview_has_no_host_credentials_or_input(self):
        p = plan()
        self.assertEqual(p["relative_path"], "/v1/responses")
        self.assertEqual(p["method"], "POST")
        self.assertFalse(p["body_included"])
        self.assertFalse(p["authorization_header_included"])
        self.assertFalse(p["target_host_included"])
        self.assertNotIn("Authorization", p["headers"])
        self.assertNotIn("Read README", str(p))
        self.assertNotIn("https://", str(p))

    def test_protocol_header_pinned(self):
        p = plan()
        self.assertEqual(p["headers"]["UHP-Version"], "2026-10-19")
        self.assertEqual(p["headers"]["Content-Type"], "application/json")
        self.assertEqual(p["headers"]["Idempotency-Key"], p["idempotency_key"])

    def test_same_request_same_retry_identity(self):
        self.assertEqual(plan(), plan())

    def test_independent_order_changes_identity(self):
        req, contract = compile_task(
            {**order(), "work_order_id": "work-different"}, capabilities()
        )
        another = compile_transport_preview(req, contract, discovery())
        self.assertNotEqual(plan()["idempotency_key"], another["idempotency_key"])

    def test_mutated_request_detected(self):
        req, contract = compile_task(order(), capabilities())
        req["input"] = "different input"
        with self.assertRaises(UHPContractError):
            compile_transport_preview(req, contract, discovery())

    def test_mutated_request_metadata_detected(self):
        req, contract = compile_task(order(), capabilities())
        req["metadata"]["harness_id"] = "chrn:other"
        with self.assertRaises(UHPContractError):
            compile_transport_preview(req, contract, discovery())

    def test_model_mutation_detected(self):
        req, contract = compile_task(order(), capabilities())
        req["model"] = "other"
        with self.assertRaises(UHPContractError):
            compile_transport_preview(req, contract, discovery())

    def test_unauthorized_dispatch_contract_rejected(self):
        req, contract = compile_task(order(), capabilities())
        contract["dispatch_authorized"] = True
        with self.assertRaises(UHPContractError):
            compile_transport_preview(req, contract, discovery())

    def test_false_authority_claim_rejected(self):
        req, contract = compile_task(order(), capabilities())
        contract["canonical_authority_delta"] = "A5"
        with self.assertRaises(UHPContractError):
            compile_transport_preview(req, contract, discovery())

    def test_false_capability_claim_rejected(self):
        req, contract = compile_task(order(), capabilities())
        contract["capability_claim"] = "VERIFIED"
        with self.assertRaises(UHPContractError):
            compile_transport_preview(req, contract, discovery())

    def test_unauthenticated_discovery_does_not_attest_security(self):
        p = plan()
        self.assertEqual(set(p["external_gates"].values()), {"HOLD"})
        self.assertEqual(len(p["external_gates"]), 9)

    def test_discovery_version_and_protocol_required(self):
        req, contract = compile_task(order(), capabilities())
        for k, v in (("protocol", "not-uhp"), ("versions", ["2026-09-28"])):
            d = discovery()
            d[k] = v
            with self.assertRaises(UHPContractError):
                compile_transport_preview(req, contract, d)

    def test_advertised_idempotency_required(self):
        req, contract = compile_task(order(), capabilities())
        for val in (False, "true", None):
            d = discovery()
            d["capabilities"]["idempotency"] = val
            with self.assertRaises(UHPContractError):
                compile_transport_preview(req, contract, d)

    def test_no_stream_store_tools_include_url(self):
        req, contract = compile_task(order(), capabilities())
        for k, v in (("stream", True), ("store", True),
                     ("tools", []), ("include", []),
                     ("url", "http://127.0.0.1")):
            r = copy.deepcopy(req)
            r[k] = v
            with self.subTest(field=k), self.assertRaises(UHPContractError):
                compile_transport_preview(r, contract, discovery())

    def test_environment_binding(self):
        o = order()
        o["environment_id"] = "henv:synthetic"
        req, contract = compile_task(o, capabilities())
        result = compile_transport_preview(req, contract, discovery())
        self.assertFalse(result["dispatch_authorized"])
        req["metadata"]["environment"] = "henv:other"
        with self.assertRaises(UHPContractError):
            compile_transport_preview(req, contract, discovery())

    def test_budget_and_input_limits(self):
        req, contract = compile_task(order(), capabilities())
        for field, value in (("max_step", True), ("timeout_seconds", 10000),
                             ("input", "")):
            r = copy.deepcopy(req)
            r[field] = value
            with self.subTest(field=field), self.assertRaises(UHPContractError):
                compile_transport_preview(r, contract, discovery())

    def test_retry_same_request_unknown_outcome_does_not_auto_run(self):
        p = plan()
        verdict = assess_retry(p, p, "UNKNOWN_OUTCOME")
        self.assertEqual(verdict["verdict"], "EXTERNAL_IDEMPOTENCY_WITNESS_REQUIRED")
        self.assertFalse(verdict["retry_authorized"])

    def test_retry_completely_finished_does_not_replay(self):
        p = plan()
        self.assertEqual(assess_retry(p, p, "COMPLETED")["verdict"],
                         "COMPLETED_NO_REPLAY")

    def test_retry_collision_on_changed_request(self):
        old = plan()
        new = copy.deepcopy(old)
        new["request_sha256"] = "f" * 64
        self.assertEqual(assess_retry(old, new, "UNKNOWN_OUTCOME")["verdict"],
                         "RETRY_BINDING_COLLISION_HOLD")

    def test_retry_collision_on_changed_source(self):
        old = plan()
        new = copy.deepcopy(old)
        new["source_digest"] = "sha256:" + "b" * 64
        self.assertEqual(assess_retry(old, new, "NOT_SENT")["verdict"],
                         "RETRY_BINDING_COLLISION_HOLD")

    def test_retry_other_work_order(self):
        old = plan()
        new = copy.deepcopy(old)
        new["work_order_id"] = "different"
        self.assertEqual(assess_retry(old, new, "NOT_SENT")["verdict"],
                         "DIFFERENT_WORK_ORDER_NOT_A_RETRY")

    def test_retry_unknown_state_rejected(self):
        p = plan()
        with self.assertRaises(UHPContractError):
            assess_retry(p, p, "AUTO_RETRY")

    def test_retry_mutated_endpoint_rejected(self):
        p = plan()
        new = copy.deepcopy(p)
        new["relative_path"] = "/v1/secrets"
        with self.assertRaises(UHPContractError):
            assess_retry(p, new, "UNKNOWN_OUTCOME")

    def test_retry_header_tampering_rejected(self):
        p = plan()
        new = copy.deepcopy(p)
        new["headers"]["Idempotency-Key"] = "changed"
        with self.assertRaises(UHPContractError):
            assess_retry(p, new, "UNKNOWN_OUTCOME")

    def test_plan_never_certifies_sources_or_harness(self):
        p = plan()
        self.assertEqual(p["external_gates"]["source_content"], "HOLD")
        self.assertEqual(p["external_gates"]["harness_permissions"], "HOLD")
        self.assertEqual(p["external_gates"]["hard_tool_enforcement"], "HOLD")


if __name__ == "__main__":
    unittest.main()
