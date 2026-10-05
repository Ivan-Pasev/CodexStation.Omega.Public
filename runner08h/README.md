# Ω Tier-A Restricted Runner Execution Pack — v0.8h

This pack is designed for an environment that already has authorized access to one of the held Tier-A repositories.

## Invariants

- It never obtains credentials.
- It never clones a restricted repository into Omega Public.
- It executes against an operator-supplied local Git checkout.
- The local checkout must be exactly at the frozen 08F source commit.
- The worktree must be clean before execution and remain clean afterward.
- Native command stdout/stderr is not copied into the receipt.
- Only sanitized metadata and PASS/FAIL/SKIP results are emitted.
- A receipt is evidence only after 08G admits it.

## Usage

From this runner pack repository:

```bash
python runner08h/run_source.py \
  --family NEURAL_LATTICE \
  --source-dir /path/to/authorized/neural-lattice \
  --provider LOCAL_OPERATOR \
  --run-id run-001 \
  --runner-commit "$(git rev-parse HEAD)" \
  --receipt-out neural-lattice.receipt.json
```

Inspect the plan without executing native commands:

```bash
python runner08h/run_source.py --plan --family HIGHESTONE --source-dir /path/to/authorized/HighestOne
```

Then verify and ingest the receipt using the public 08F/08G tools.

## Family scopes

- `DIGITAL_FABRICA_CORE`: TYPECHECK_BUILD only.
- `HIGHESTONE`: LEAN_KERNEL_GATE.
- `NEURAL_LATTICE`: FULL_NATIVE_VALIDATE.

A PASS is limited to the declared scope. The runner does not create authority, release eligibility, or scientific/formal promotion beyond what its native command scope directly establishes.
