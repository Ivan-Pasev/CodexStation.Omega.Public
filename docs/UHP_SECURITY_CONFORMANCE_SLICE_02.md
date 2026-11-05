# UHP Slice 02 — Static Security Review and Conformance Boundary

Date: 2026-11-05
Predecessor: UHP Slice 01 commit 113cb5236bf3b6f2ce436fc61a878023d57ecfe1
Upstream: HarnessRouter v0.38.2, UHP 2026-10-19
Scope: no external calls, no credentials, no live executable, no permission or authority change.

## Findings and disposition

S02-F01 / RESPONSE_ENVELOPE_INCOMPLETE / CORRECTED_SYNTHETIC:
The old minimal fixture omitted mandatory UHP response fields. Without strict envelope checks a malformed completed response could receive TASK_COMPLETED_EFFECT_UNVERIFIED. Now structural faults yield HOLD, and tests cover missing/wrong fields.

S02-F02 / READ_ONLY_LABEL_NOT_SANDBOX / OPEN_SECURITY_BLOCKER:
Caller-supplied effect_class READ_ONLY and hard_tool_restrictions=false are NOT evidence that the harness has disabled filesystem writes, shell, network, plugins or remote MCP. The adapter is currently non-dispatching; any future dispatcher requires independent server-side effective permissions and isolation. No prompt-only restriction is sufficient.

S02-F03 / DISCOVERY_IS_UNAUTHENTICATED / OPEN_LIVE_PROOF:
UHP GET /v1/uhp must be available without bearer token. analyze_discovery performs syntactic checks only; it does not establish TLS peer, provenance, account identity, actual available harnesses or principal scope. The private per-principal harness-list call is separate.

S02-F04 / SPEC_IMPLEMENTATION_DIALECT_DRIFT / OPEN:
UHP tasks.md describes top-level environment; environments.md and HarnessRouter current implementation use metadata.environment. This candidate follows the tested implementation; conformance of the intended server/version is required before execution.

S02-F05 / SOURCE_DIGEST_SYNTAX_NOT_AUTHENTICATION / OPEN:
A SHA-256-shaped string is not a verified source snapshot. A separate Drive/GitHub source-identity and exact-content hashing compiler is needed. The work-order proposal cannot confer canon authority.

S02-F06 / UNTRUSTED_RESPONSE_PAYLOAD / MITIGATED_OFFLINE:
A malicious/oversized response can exceed memory budgets or be non-JSON. Normalizer limits serialized envelopes to 262,144 bytes, refuses unsupported values and never promotes their outputs. A future streaming transport must enforce size before buffering.

S02-F07 / IDEMPOTENCY_AND_OUTCOME / OPEN:
No HTTP transaction, idempotency key, session recovery, duplicate response replay, cancellation, or independent effect witness exists. All are required before real execution.

S02-F08 / SECURITY_RELEASE_EXPOSURE / OPEN:
HarnessRouter 0.37.16-0.38.1 security history makes multi-member exposure and credential hygiene independently blocking. A Docker image tag is not an integrity pin. Use immutable image digest, review persistence/secret keys and perform cross-principal tests.

## Gate verdict

STATIC_CONFORMANCE_SYNTAX: CI validation in this candidate only.
SERVER_IDENTITY: HOLD
SOURCE_AUTHENTICATION: HOLD
HARD_TOOL_AND_SANDBOX_ENFORCEMENT: HOLD
LIVE_UHP_TASK: NOT_RUN
INDEPENDENT_EFFECT_CONFIRMATION: HOLD
CANONICAL_STATE_PROMOTION: HOLD
PARENT_OMEGA_09M_STABLE_WAIT: UNCHANGED

Remaining work: independently attest server/harness/version and source snapshot, then test security and isolation on an expendable instance under an explicitly authorized scope. Never infer live release eligibility from synthetic PASS.
