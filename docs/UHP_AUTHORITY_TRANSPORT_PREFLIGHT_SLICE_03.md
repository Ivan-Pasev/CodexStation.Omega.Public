# Omega UHP Slice 03 — Authority and Transport Preflight (offline)

Date: 2026-11-05
Status: DRAFT / NON-DISPATCHING / SYNTHETIC
Parent: UHP Slice 02 draft PR #30, head 5c9d2e2ed4df694431359b9c2975ab95c478494a
Source: original CodexStation integration; no HarnessRouter runtime source imported
Reference: HarnessRouter v0.38.2 / Unified Harness Protocol 2026-10-19

## Purpose

A UHP task request must not cross from *well-formed proposal* into an
*authorized execution* without independent server, principal, sandbox,
source and effects evidence.

The new runtime08c/uhp_preflight.py exports:

- compile_transport_preview(request, contract, discovery): deterministic
  offline representation of the POST /v1/responses method, relative path,
  pinned UHP-Version, content type and stable Idempotency-Key. It never
  includes raw user input, credentials, an Authorization header, a target
  URL or HTTP transport functionality.
- assess_retry(previous_plan, current_plan, last_state): distinguishes
  a retry from same work order with mutated source/request and refuses
  all automatic retries, particularly UNKNOWN_OUTCOME.

The static compiler verifies request_sha256 against the exact proposal,
checks model/harness/environment equality, requires non-streamed and
non-stored requests and enforces bounded budgets. The discovery document
must pass static protocol checks and advertise idempotency. These are only
untrusted observations: public UHP discovery does not attest server
identity, principal access or durable idempotency.

## Key constitutional invariants

DISPATCH_AUTHORIZED=false
RETRY_AUTHORIZED=false
CANONICAL_AUTHORITY_DELTA=NONE
NO_NETWORK_NO_CREDENTIALS_NO_TARGET_HOST
MUTATED_REQUEST_OR_WORK_ORDER=HOLD
UNKNOWN_OUTCOME_REQUIRES_EXTERNAL_IDEMPOTENCY_WITNESS
SERVER_DISCOVERY_NOT_PRINCIPAL_AUTHORITY
MODEL_COMPLETION_NOT_EFFECT_CONFIRMATION
READ_ONLY_INTENT_NOT_TOOL_SANDBOX_ENFORCEMENT

## Threat boundary

- A syntactically valid SHA-256 field does not prove original file
  content or trusted source ingestion.
- The planner's Idempotency-Key is not a durable deduplication journal.
  UHP servers SHOULD retain keys for at least 24 hours, not forever.
- No HTTP request is sent. A future transport needs separately approved
  pinned HTTPS/loopback origin, TLS/identity verification, origin allowlist,
  secure credential custody and bounded response streaming.
- No privileged harness, plugin, MCP, session, model, file-system or
  external API action is permitted.
- A client-supplied capability report or an agent stating it is read-only
  is insufficient to qualify technical sandbox isolation.
- A future dispatch layer MUST guard against both SSRF and duplicate
  execution after timeouts/UNKNOWN_OUTCOME; silent retry is forbidden.
- Only an independent effects witness can promote a completed task to
  verified effects, and only the canonical governance process can
  authorize promotion.

## Verification and release

Run: python -m unittest -v tests.test_uhp_preflight
Run all: python -m unittest discover -s tests -v
No deployment, no merge, no live harness run, no private corpus source,
no MLCO/UKC mutation, no release status change.

Open gates: authenticated principal-scoped harness listing, server
origin and TLS pinning, hard restriction/sandbox proof, source snapshot
digest verification, credential isolation, durable idempotency journal,
live disposable task, independent effect observer and 09M release holds.
