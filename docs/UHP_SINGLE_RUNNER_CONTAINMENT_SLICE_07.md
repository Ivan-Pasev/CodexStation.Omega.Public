# Omega UHP Slice 07 — Single-runner disposable containment smoke

Date: 2026-11-05
Classification: STACKED DRAFT / LIMITED CI EXECUTION / NOT TWO-HOST QUALIFICATION
Parent: Slice 06 PR #35 exact head 0ebf3e57a2d57f7bdcc80741782f2d402f1e3931
No original UHP task, model, provider credential, real source corpus, or deployment.

## What is executable

A separate isolated GitHub Actions job runs a fixed Go standard-library
probe, compiled locally from the exact PR checkout into a FROM scratch
container. It never pulls a base image or depends on a model/provider.

Docker isolation flags:
- network none; read-only rootfs; all Linux capabilities dropped;
- no-new-privileges; pids-limit 32; memory 128 MiB; CPU 0.5;
- explicit UID/GID 65534; no elevated daemon or privileged sockets;
- exact synthetic fixture bind at /source, read-only; no other binds.

The fixed probe checks that reading synthetic source succeeds, source
modification is denied, creating a file in the rootfs is denied, connecting
to a reserved documentation IP fails, and the Docker socket is inaccessible.
The host runner, not the worker, collects Docker inspect, container exit
code and fixture SHA-256 before/after. Pure Python validation checks that
inspect-reported flags match the fixed plan, exit code is zero and source
checksum unchanged. A bounded artifact stores only the nonauthorizing review.

No guest output alone is sufficient; the host inspects runtime flags.
Nevertheless, the same CI runner controls both executor and observation.
A successful probe is a single-runner smoke observation, not an independent,
cryptographically authenticated two-host witness. TCP failure alone is not
proof of egress disabled; Docker network-mode inspection is also required.

## Relation to the Slice 06 matrix

Partially exercised on one disposable CI runner:
- N01 protected synthetic source write denied;
- N03 network mode none plus denied fixed TCP attempt;
- N06 no Docker daemon socket exposed (not comprehensive escalation test);
- N12 before/after synthetic fixture SHA-256 equality on same runner.

Not independently exercised: N02 observer-only evidence-store denial,
N04 credential canary compartment, N05 traversal adversarial probe,
N07 cross-principal artifact isolation, N08 artifact corruption,
N09 durable replay rejection, N10 immutable-source pin mismatch,
N11 uncertain UHP retry semantics. No independent two-host qualification
exists for any probe, including those exercised in single-runner CI.

All C01–C12 / N01–N12 owner-controlled gates remain OPEN. Legacy 09H
LIVE_HOST labels remain shape classifications, not authenticated machines.

## Why the receipt cannot grant authority

Best possible verdict: SINGLE_RUNNER_SMOKE_SHAPE_ONLY.
It does not prove independent hosts, trusted acquisition, signer custody,
replay persistence, secure time, full seccomp/confinement, actual UHP
principal authorization, real task execution, effects, cost or privacy.

All receipts retain false values for independent_host_verified,
separate_observer_verified, technical_isolation_independently_verified,
network_egress_independently_verified, external_effects_verified,
real_uhp_task_executed, dispatch_authorized, retry_authorized and
promotion_authorized. canonical_authority_delta stays NONE.

## Files and reproduction

runtime08c/uhp_ci_containment.py — pure reviewer.
tests/test_uhp_ci_containment.py — static/adversarial tests.
ops/uhp07/worker_probe.go — fixed negative probe.
ops/uhp07/run_ci_probe.sh — ephemeral scratch-image run and cleanup.
.github/workflows/uhp07-smoke.yml — isolated CI job.
docs/UHP_SINGLE_RUNNER_CONTAINMENT_SLICE_07.md — this record.

Run python -m unittest discover -s tests -v.
The separate GitHub CI job runs a public fixed fixture, no live UHP model,
provider service, user secret, installed host agent or independent observer.

## Promotion boundary

Next operational closure requires the owner-authorized two-host pilot
specified in Slice 06, independent signed capture, complete negative-test
matrix, immutable source pin, protected key registry and durable nonce
and idempotency journal. No merge, release approval or 09M STABLE_WAIT
change follows from a passing single-runner smoke test.
