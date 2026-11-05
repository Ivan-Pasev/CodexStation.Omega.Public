"""UHP08 CI smoke: adversarial contract tests, no Docker or host runtime here."""
import copy
import unittest

from runtime08c.uhp_adapter import UHPContractError
from runtime08c.uhp_ci_containment import assess_ci_containment

A = "a" * 64
B = "b" * 64


def inspected():
    return {
        "HostConfig": {
            "NetworkMode": "none", "ReadonlyRootfs": True,
            "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"],
            "Privileged": False, "Memory": 134217728,
            "PidsLimit": 32, "NanoCpus": 500000000,
            "PidMode": "", "IpcMode": "private", "Devices": [],
        },
        "Config": {"User": "65534:65534", "Entrypoint": ["/worker"]},
        "State": {"ExitCode": 0, "Running": False},
        "Mounts": [{
            "Type": "bind", "Destination": "/source", "RW": False,
        }],
    }


def check(i=None, code=0, before=A, after=A):
    return assess_ci_containment(
        inspected() if i is None else i, code, before, after,
    )


class UHP08ContainmentTests(unittest.TestCase):
    def test_synthetic_shape_cannot_promote(self):
        result = check()
        self.assertEqual(result["verdict"], "SINGLE_RUNNER_SMOKE_SHAPE_ONLY")
        self.assertEqual(result["reasons"], [])
        self.assertTrue(result["source_snapshot_unchanged"])
        for key in (
            "independent_host_verified", "separate_observer_verified",
            "technical_isolation_independently_verified",
            "network_egress_independently_verified",
            "source_capture_provenance_verified", "durable_replay_verified",
            "external_effects_verified", "real_uhp_task_executed",
            "dispatch_authorized", "retry_authorized", "promotion_authorized",
        ):
            self.assertFalse(result[key], key)
        self.assertEqual(result["canonical_authority_delta"], "NONE")

    def test_network_mode_bridge_holds(self):
        x = inspected()
        x["HostConfig"]["NetworkMode"] = "bridge"
        self.assertIn("NETWORK_NOT_DISABLED", check(x)["reasons"])

    def test_rootfs_write_flag_holds(self):
        x = inspected()
        x["HostConfig"]["ReadonlyRootfs"] = False
        self.assertEqual(check(x)["verdict"], "HOLD")

    def test_capabilities_present_holds(self):
        x = inspected()
        x["HostConfig"]["CapDrop"] = ["NET_ADMIN"]
        self.assertIn("CAPABILITIES_NOT_DROPPED", check(x)["reasons"])

    def test_new_privileges_possible_holds(self):
        x = inspected()
        x["HostConfig"]["SecurityOpt"] = []
        self.assertIn("PRIVILEGE_ESCALATION_NOT_FORBIDDEN", check(x)["reasons"])

    def test_privileged_container_holds(self):
        x = inspected()
        x["HostConfig"]["Privileged"] = True
        self.assertIn("PRIVILEGED_CONTAINER", check(x)["reasons"])

    def test_root_user_holds(self):
        x = inspected()
        x["Config"]["User"] = "0:0"
        self.assertIn("USER_NOT_EXPLICITLY_NONROOT", check(x)["reasons"])

    def test_other_entrypoint_holds(self):
        x = inspected()
        x["Config"]["Entrypoint"] = ["/bin/sh"]
        self.assertIn("UNEXPECTED_EXECUTABLE", check(x)["reasons"])

    def test_memory_unbounded_holds(self):
        x = inspected()
        x["HostConfig"]["Memory"] = 0
        self.assertIn("MEMORY_LIMIT_MISSING", check(x)["reasons"])

    def test_pid_budget_unbounded_holds(self):
        x = inspected()
        x["HostConfig"]["PidsLimit"] = 0
        self.assertIn("PID_LIMIT_MISSING", check(x)["reasons"])

    def test_cpu_budget_unbounded_holds(self):
        x = inspected()
        x["HostConfig"]["NanoCpus"] = 0
        self.assertIn("CPU_LIMIT_MISSING", check(x)["reasons"])

    def test_host_pid_namespace_holds(self):
        x = inspected()
        x["HostConfig"]["PidMode"] = "host"
        self.assertIn("HOST_PID_NAMESPACE_PRESENT", check(x)["reasons"])

    def test_host_ipc_namespace_holds(self):
        x = inspected()
        x["HostConfig"]["IpcMode"] = "host"
        self.assertIn("HOST_IPC_NAMESPACE_PRESENT", check(x)["reasons"])

    def test_privileged_device_holds(self):
        x = inspected()
        x["HostConfig"]["Devices"] = [{"PathOnHost": "/dev/kvm"}]
        self.assertIn("EXTRA_DEVICES_PRESENT", check(x)["reasons"])

    def test_writable_mount_holds(self):
        x = inspected()
        x["Mounts"][0]["RW"] = True
        self.assertIn("SOURCE_MOUNT_NOT_READONLY", check(x)["reasons"])

    def test_mount_not_source_holds(self):
        x = inspected()
        x["Mounts"][0]["Destination"] = "/root"
        self.assertIn("SOURCE_MOUNT_NOT_READONLY", check(x)["reasons"])

    def test_extra_mount_holds(self):
        x = inspected()
        x["Mounts"].append({"Type": "volume", "Destination": "/secret", "RW": False})
        self.assertIn("UNEXPECTED_MOUNT_COUNT", check(x)["reasons"])

    def test_missing_mount_holds(self):
        x = inspected()
        x["Mounts"] = []
        self.assertEqual(check(x)["verdict"], "HOLD")

    def test_exit_code_inconsistent_holds(self):
        x = inspected()
        x["State"]["ExitCode"] = 42
        self.assertIn("EXIT_CODE_NOT_INDEPENDENTLY_MATCHED", check(x)["reasons"])

    def test_running_state_holds(self):
        x = inspected()
        x["State"]["Running"] = True
        self.assertIn("EXIT_CODE_NOT_INDEPENDENTLY_MATCHED", check(x)["reasons"])

    def test_worker_denial_probe_failure_holds(self):
        x = inspected()
        x["State"]["ExitCode"] = 42
        self.assertIn("NEGATIVE_PROBE_WORKER_FAILED", check(x, code=42)["reasons"])

    def test_mutated_source_holds(self):
        result = check(after=B)
        self.assertIn("SOURCE_SNAPSHOT_CHANGED", result["reasons"])

    def test_malformed_digest_rejected(self):
        with self.assertRaises(UHPContractError):
            check(before="SHA256:abc")
        with self.assertRaises(UHPContractError):
            check(after="0" * 63)

    def test_boolean_exit_rejected(self):
        with self.assertRaises(UHPContractError):
            check(code=False)

    def test_missing_inspect_rejected(self):
        with self.assertRaises(UHPContractError):
            assess_ci_containment(None, 0, A, A)

    def test_nonobject_hostconfig_rejected(self):
        x = inspected()
        x["HostConfig"] = "none"
        with self.assertRaises(UHPContractError):
            check(x)

    def test_duplicate_or_absurd_mount_list_rejected(self):
        x = inspected()
        x["Mounts"] = [{} for _ in range(17)]
        with self.assertRaises(UHPContractError):
            check(x)

    def test_result_does_not_embed_privileged_host_data(self):
        x = inspected()
        x["Config"]["Env"] = ["EXAMPLE_PRIVATE_CANARY=secret"]
        r = check(x)
        self.assertNotIn("EXAMPLE_PRIVATE_CANARY", str(r))
        self.assertNotIn("secret", str(r))

    def test_nonmutating(self):
        x = inspected()
        before = copy.deepcopy(x)
        check(x)
        self.assertEqual(x, before)

    def test_stable_deterministic_review(self):
        self.assertEqual(check(), check())


if __name__ == "__main__":
    unittest.main()
