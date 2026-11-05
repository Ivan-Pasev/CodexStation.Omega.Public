# Omega UHP Adapter — Candidate Slice 01

**State:** NON-DISPATCHING / SYNTHETIC / NO RELEASE AUTHORITY.
**Pinned parent:** Omega Public 09N a60e793b80f655d088120383e894b3fa4953820c.
**Upstream reference:** HarnessRouter v0.38.2 / UHP 2026-10-19.
**Provenance:** Original integration code; no upstream code transplanted.

This slice extends the existing Omega 08C adapter layer without replacing any constitutional runtime or altering a release manifest.

## Interface

- compile_task(work_order, capability_record) -> (proposed UHP request, non-authorizing binding contract).
- normalize_response(binding_contract, UHP response) -> non-authorizing observation.

The compiler only produces strictly bounded READ_ONLY candidates and rejects all requests that need qualified hard-tool restrictions. It cannot invoke an HTTP endpoint, launch an agent, sign an approval, or write canonical state.

UHP metadata carries harness_id. Environment binding uses metadata.environment in HarnessRouter v0.38.2 implementation and environments.md; tasks.md states top-level environment, a documented conflict that MUST be resolved by live conformance before dispatch.

UHP status completed means task lifecycle completion, NEVER effect verification, scientific confirmation, release qualification, or canonical authority.

## Invariants

1. DISPATCH_AUTHORIZED=false; PROMOTION_AUTHORIZED=false.
2. SOURCE_PIN_REQUIRED, UHP_VERSION_PIN_REQUIRED, HARNESS_AND_MODEL_FIDELITY.
3. Tool restrictions required for safety but not hard-enforced => HOLD.
4. Unauthorized or malformed inputs => fail closed.
5. Unknown or ignored contract fields and model fallback => HOLD.
6. Successful task => EFFECT_CONFIRMATION=UNKNOWN_OUTCOME.
7. Parent 09M stable wait and all existing evidence/release holds remain unchanged.

## Reproduce

python -m unittest -v tests.test_uhp_adapter
python -m unittest discover -s tests -v

No real network, provider credentials, host installation, environment build, actual model execution, tool enforcement qualification, Omnius dispatch, or release has been performed by this candidate.

## Slice 02 security corrections

The earlier synthetic response fixture omitted protocol-required response fields. The 02 candidate now checks object identity, timestamp, output, usage, session binding, previous response link, requested persistence, error/incomplete consistency, critical ignored request fields, model substitution and bounded JSON envelope. An incomplete or inconsistent envelope holds rather than claiming task completion.

Pure analyze_discovery() examines a supplied GET /v1/uhp document's shape but cannot authenticate a server. UHP discovery is intentionally unauthenticated; actual principal-scoped harness inventory must be independently established. A syntactically correct source hash is not proof of source contents, and READ_ONLY is intent, never tool containment. No real dispatch may be enabled from these source checks.

## Next gate

Independent review; hosted CI across Python 3.11-3.13; exact server version/capability attestation; non-privileged disposable-harness live conformance; then a separately authorized execution membrane.
