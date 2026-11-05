# Omega UHP Slice 10 — Established-CI Containment Smoke Gate

Date: 2026-11-05
Status: STACKED DRAFT / EXACT-HEAD CI REQUIRED
Canonical parent: Slice 09 draft PR #40, exact head
91abddb87516d47b8f0b31ce755d1ff7a8a941a9.

## Purpose

Slice 08 introduced the static Go disposable negative-probe worker and
separate uhp08-smoke.yml workflow; Slice 09 created conservative coverage
mapping. The separate smoke workflow did not have a verified exact-head
run for canonical Slice 08 even though the earlier superseded PR #37
ran its own smoke successfully. The established public-omega-ci PR run
was green for Slice 08 and Slice 09, but this did not exercise Docker
on those exact heads.

This child integrates one new independent job into the existing
.github/workflows/ci.yml, the workflow already verified to run on
both push and PR events for the canonical stack. It performs exactly
the fixed ops/uhp08/run_ci_probe.sh workflow and uploads the existing
non-authorizing JSON receipt as a short-lived CI artifact. This is a
CI gate wiring change, NOT a change in the core UHP runtime, public
protocol or authorization semantics.

## Containment model

Worker: fixed public Go source (stdlib only), compiled into
scratch container; no registry image, package download, model,
private data or real provider secrets.

Execution flags on disposable GitHub-hosted runner: network none,
read-only root/source bind, all caps dropped, no-new-privileges,
nonroot UID/GID, CPU/memory/process bounds.

The job fails on unexpected worker success of prohibited actions,
unexpected Docker runtime configuration, nonzero worker exit, or
changed synthetic source checksum. The job does not trust worker text
as proof; host Docker inspect is checked as supplied local metadata.

## Non-claims and remaining gates

This CI job is operated on ONE GitHub Actions runner. It does not
establish a second, independently controlled observer host, protected
observer key custody, trusted time, durable replay, two-machine
source capture, real network egress equivalence, a production
sandbox, actual UHP server operation or independent effects.

Highest possible assessment: SINGLE_RUNNER_SMOKE_SHAPE_ONLY.

The full C01–C12 / N01–N12 matrix remains externally UNQUALIFIED.
Even if PR CI passes and a real single-runner smoke log/artifact exists:
- dispatch_authorized=false
- retry_authorized=false
- promotion_authorized=false
- canonical_authority_delta=NONE
- Omega NEXT 09M STABLE_WAIT unchanged
- RELEASE_ELIGIBLE=false

## Verification and status discipline

Before any CI-positive claim, read the exact-head GitHub Actions
run, verify all 3 Python matrix jobs and the separate
uhp-single-runner-smoke job completed successfully, inspect the
negative-probe log and the receipt artifact's provenance.

A failed CI scheduling attempt must be distinguished from a
passed test on a separate trigger or ancestor commit; passing
a different commit does not close this exact-head gate.

Next: owner-approved independent two-host pilot with external
custody, durable replay and all negative-probe evidence. No
automatic live dispatch, branch merge or plugin installation.
