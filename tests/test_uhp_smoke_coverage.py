"""Regression for partial CI smoke bridge: never claim twelve-probe closure."""
import copy
import json
import unittest
from pathlib import Path
from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_ci_containment import assess_ci_containment
from runtime08c.uhp_smoke_coverage import reconcile_ci_smoke

SOURCE = "a" * 64
MATRIX_FILE = Path(__file__).resolve().parents[1] / "ops/uhp06/qualification_matrix.json"


def matrix():
    return json.loads(MATRIX_FILE.read_text())


def smoke(inspect=None, after=SOURCE):
    obj = {
        "HostConfig": {"NetworkMode":"none","ReadonlyRootfs":True,
                       "CapDrop":["ALL"],"SecurityOpt":["no-new-privileges"],
                       "Privileged":False,"Memory":134217728,"PidsLimit":32,
                       "NanoCpus":500000000,"PidMode":"","IpcMode":"private",
                       "Devices":[]},
        "Config": {"User":"65534:65534","Entrypoint":["/worker"]},
        "State": {"ExitCode":0,"Running":False},
        "Mounts": [{"Type":"bind","Destination":"/source","RW":False}],
    }
    if inspect == "network-bridge":
        obj["HostConfig"]["NetworkMode"] = "bridge"
        inspect = None
    return assess_ci_containment(obj if inspect is None else inspect,0,SOURCE,after)


def bridge(m=None, r=None):
    return reconcile_ci_smoke(matrix() if m is None else m,
                              smoke() if r is None else r)


class SmokeCoverageTests(unittest.TestCase):
    def test_four_partial_not_twelve(self):
        result=bridge()
        self.assertEqual(result["verdict"],"PARTIAL_SINGLE_RUNNER_RESEARCH_ONLY")
        self.assertEqual([x["probe_id"] for x in result["partially_exercised"]],
                         ["N01","N03","N06","N12"])
        self.assertEqual(len(result["not_exercised"]),8)
        self.assertEqual(result["externally_qualified_probe_ids"],[])
        self.assertFalse(result["full_matrix_qualified"])

    def test_non_authorizing(self):
        r=bridge()
        for key in ("independent_observer_verified",
                    "two_host_qualification_verified","durable_replay_verified",
                    "actual_uhp_task_executed","dispatch_authorized",
                    "retry_authorized","promotion_authorized"):
            self.assertFalse(r[key])

    def test_deterministic(self):
        self.assertEqual(bridge(),bridge())

    def test_bad_network_is_hold(self):
        r=smoke(inspect="network-bridge")
        self.assertEqual(bridge(r=r)["verdict"],"HOLD")

    def test_source_change_is_hold(self):
        self.assertEqual(bridge(r=smoke(after="b"*64))["verdict"],"HOLD")

    def test_forged_smoke_authority_refused(self):
        r=smoke()
        r["promotion_authorized"]=True
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_forged_independent_origin_refused(self):
        r=smoke()
        r["independent_host_verified"]=True
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_source_hash_disagreement_refused(self):
        r=smoke()
        r["source_snapshot_unchanged"]=False
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_opaque_release_verdict_refused(self):
        r=smoke()
        r["verdict"]="AUTHORIZED"
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_unknown_authority_delta_refused(self):
        r=smoke()
        r["canonical_authority_delta"]="PROMOTED"
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_incorrect_matrix_expected_denial_refused(self):
        m=matrix()
        m["negative_probes"][0]["expected"]="MATCH"
        with self.assertRaises(UHPContractError):
            bridge(m=m)

    def test_missing_matrix_probe_refused(self):
        m=matrix()
        m["negative_probes"].pop()
        with self.assertRaises(UHPContractError):
            bridge(m=m)

    def test_duplicate_matrix_probe_refused(self):
        m=matrix()
        m["negative_probes"][0]["id"]="N02"
        with self.assertRaises(UHPContractError):
            bridge(m=m)

    def test_holding_smoke_has_no_coverage(self):
        r=smoke()
        r["verdict"]="HOLD"
        r["reasons"]=["fixture_fail"]
        result=bridge(r=r)
        self.assertEqual(result["partially_exercised"],[])
        self.assertEqual(len(result["not_exercised"]),12)

    def test_unexecuted_claim_is_refused(self):
        r=smoke()
        r["single_runner_probe_executed"]=False
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_tamper_reason_type_refused(self):
        r=smoke()
        r["reasons"]=[123]
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_live_host_label_smuggling_rejected(self):
        r=smoke()
        r["witness_origin"]="LIVE_HOST"
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_missing_receipt_field_rejected(self):
        r=smoke()
        del r["inspect_shape_consistent"]
        with self.assertRaises(UHPContractError):
            bridge(r=r)

    def test_all_input_preserved(self):
        m,r=matrix(),smoke()
        prev=copy.deepcopy((m,r))
        reconcile_ci_smoke(m,r)
        self.assertEqual((m,r),prev)


if __name__=="__main__":
    unittest.main()
