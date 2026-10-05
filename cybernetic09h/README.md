# Omega Host Witness Runner Pack v0.9h

This pack generates a 09G-compatible host witness from deterministic policy replay.

## Origin rule

The runner itself cannot establish that it is executing on a registered live host.

Without an attestation, it emits:

`witness_origin = REFERENCE_IMPLEMENTATION`

To emit `LIVE_HOST`, supply a host-origin attestation that matches the registered host id and host-profile digest and contains:
- `attestation_class = HOST_BOUND_RUNTIME`
- runtime channel
- execution id
- non-empty evidence references

This is a provenance claim, not trusted-hardware proof or governance authority.

## Example

```bash
python cybernetic09h/run_host_witness.py \
  --host-id chatgpt-codex \
  --attestation host-attestation.json \
  --out chatgpt-codex.witness.json
```

The resulting witness should then be verified by the 09G conformance gate. The live registry is not mutated by the runner.
