This repository stores benchmark results in two formats:

- `data/results.jsonl` — **source of truth** (canonical schema; one JSON object per line).
- `data/results.csv` — derived for convenience and backward-compatible reporting.
  It is regenerated from JSONL by `scripts/parse_bench.py` and MUST NOT be edited manually.

## Canonical keys (JSONL)

Every record intended for reporting MUST provide the canonical fields below.

Required:
- `ts_utc` (string, RFC3339 UTC, e.g. `2026-01-14T01:08:28Z`)
- `repo` (string)
- `commit` (string)
- `scheme` (string)
- `bench_name` (string)
- `chain_profile` (string; normalized, e.g. `EVM/L1`, `EVM/L2`)
- `gas` (int) — measured gas for the surface under test
- `denominator` (string) — security metric name (e.g. `lambda_eff`, `sec_equiv_bits`)
- `denom_bits` (number) — denominator value in bits
- `gas_per_bit` (number) — `gas / denom_bits`

Recommended (used to avoid scope-mixing and “wormholes”):
- `surface_id` (string) — canonical surface taxonomy id, e.g. `zk::groth16_bn254::pairing4`
- `lane_assumption` (string) — `explicit` | `implicit` | `unknown`
- `wiring_lane` (string) — lane id (see `spec/explicit_lanes.md`)

Optional metadata:
- `hash_profile` (string)
- `security_model` (string)
- `surface_class` (string)
- `key_storage_assumption` (string; see `spec/key_storage_assumption.md`)
- `aggregation_mode` (string)
- `depends_on` (string | string[])
- `notes` (string)
- `provenance` (object) — runner/path and optional upstream repo/commit overrides
- `vector_pack_ref` / `vector_pack_id` / `vector_id` (strings)

## Legacy keys (CSV / report compatibility)

Reports and CSV headers use legacy names. To keep compatibility, every canonical record MUST
also be representable in legacy form.

Legacy equivalents:
- `gas_verify`            := `gas`
- `security_metric_type`  := `denominator`
- `security_metric_value` := `denom_bits`
- `gas_per_secure_bit`    := `gas_per_bit`

Rule:
- `scripts/parse_bench.py` MUST enforce **canonical → legacy** mapping automatically so new benches
  (Falcon, Dilithium, ZK surfaces) show up in both JSONL and CSV/reports without special casing.

## Lanes / domain separation

When a benchmark is intended for cross-project comparison, it SHOULD declare:
- `lane_assumption = "explicit"`
- `wiring_lane = ...` (e.g. `EVM_SIG_LANE_V0`, `EVM_ZK_FROM_PQ_LANE_V0`)

See `spec/explicit_lanes.md` for the lane envelope and canonical lane ids.
### surface_id (string)

Verification surface classification (minimal v0):

- `sig::app` — app-facing boundary (ERC-1271 / ERC-7913 / AA wrappers)
- `sig::protocol` — protocol-facing boundary (precompile / enshrined verifier boundary, e.g., candidate EIP-7932 class)
- `zk::settlement` — L1 settlement verifier boundary (proof verification surfaces, e.g., BN254/Groth16)
- `entropy::protocol` — protocol entropy surfaces (RANDAO mix, attestation relay, etc.)

### method (string)

Verification method (minimal v0):

- `native` — direct verification of the primitive/algorithm
- `preA` — optimized path using precomputed/transmitted `A_ntt` (e.g., ML-DSA PreA `compute_w`)
- `zk_proxy_groth16_bn254` — “PQ inside SNARK”, L1 verifies Groth16 on BN254 (+ calldata/public inputs)
