// Slice 08 fixed, synthetic negative probes. No agent, model, secrets, or provider.
// Run only inside the network-disabled, read-only, unprivileged container.
package main

import (
	"fmt"
	"net"
	"os"
	"time"
)

func markDenied(label string, err error) bool {
	if err == nil {
		fmt.Printf("%s: UNEXPECTED_ALLOWED\n", label)
		return false
	}
	fmt.Printf("%s: DENIED_AS_PROBED\n", label)
	return true
}

func main() {
	ok := true
	if os.Geteuid() != 65534 {
		fmt.Println("nonroot: UNEXPECTED_UID")
		ok = false
	} else {
		fmt.Println("nonroot: UID_65534")
	}

	// Source must remain readable. Source write must be denied by the
	// container's readonly bind mount, independent of POSIX file mode.
	contents, err := os.ReadFile("/source/fixture.txt")
	if err != nil || string(contents) != "CODEXSTATION_UHP08_PUBLIC_SYNTHETIC_FIXTURE\n" {
		fmt.Println("source_read: FAILED")
		ok = false
	} else {
		fmt.Println("source_read: FIXTURE_MATCH")
	}
	if !markDenied("source_write", os.WriteFile("/source/fixture.txt", []byte("changed"), 0600)) {
		ok = false
	}
	if !markDenied("rootfs_write", os.WriteFile("/unexpected-write", []byte("changed"), 0600)) {
		ok = false
	}
	// Reserved documentation IP. A blocked connection alone does not prove
	// no network: CI must ALSO independently inspect NetworkMode == "none".
	conn, dialErr := net.DialTimeout("tcp", "192.0.2.1:443", 900*time.Millisecond)
	if conn != nil {
		_ = conn.Close()
	}
	if !markDenied("external_tcp_connect", dialErr) {
		ok = false
	}
	// The daemon socket is intentionally not mounted inside the worker.
	f, sockErr := os.Open("/var/run/docker.sock")
	if f != nil {
		_ = f.Close()
	}
	if !markDenied("docker_socket_read", sockErr) {
		ok = false
	}
	if ok {
		fmt.Println("synthetic_probe: FINISHED_DENIAL_CHECKS")
		return
	}
	fmt.Println("synthetic_probe: FAIL_CLOSED")
	os.Exit(42)
}
