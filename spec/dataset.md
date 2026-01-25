# Dataset schema (data/results.jsonl)

This repo’s canonical dataset is `data/results.jsonl` (append-only, one JSON object per line).
`data/results.csv` is derived from it.

## Required fields (per row)

- `ts_utc` (string, ISO-8601 Z)
- `scheme` (string) — e.g. `mldsa65_fips204`, `zk_groth16_bn254`
- `bench_name` (string) — stable identifier for this benchmark
- `surface_id` (string) — taxonomy node (e.g. `sig::erc7913`, `aa::validateUserOp`, `sig::zk_from_pq::...`)
- `method` (string) — verification method (e.g. `native`, `preA`, `zk_proxy_groth16_bn254`)
- `chain_profile` (string) — e.g. `evm_l1`, `evm_l2`
- `gas` (int) — single-run snapshot gas

### Denominator (normalization)

- `denominator` (string) — e.g. `lambda_eff`, `security_equiv_bits`
- `denom_bits` (int) — the bit-count used for normalization

### Provenance

- `repo` (string)
- `commit` (string)

### Notes

- `notes` (string) — short human-readable details (calldata sizes, assumptions, etc.)

## Lane metadata (wormhole prevention)

Benchmarks intended for cross-project comparison MUST declare lane metadata.

- `lane_assumption` (enum):
  - `explicit` — benchmark binds/assumes an explicit lane envelope
  - `none` — explicitly no lane binding
  - `implicit` — lane-like binding exists but not standardized / not declared
  - `unknown`

- `wiring_lane` (enum):
  - `EVM_SIG_LANE_V0` — native EVM signature verification surfaces
  - `EVM_ZK_FROM_PQ_LANE_V0` — ZK enforcement on L1 derived from PQ signatures (proof verifier gas + calldata)
  - `none`

### Rules

- If `lane_assumption == "explicit"` then `wiring_lane` MUST NOT be `none`.
- `EVM_SIG_LANE_V0` is for native signature verification (Solidity / ERC-1271 / ERC-7913 / AA validateUserOp).
- `EVM_ZK_FROM_PQ_LANE_V0` is for proof-based enforcement (e.g., Groth16 BN254 verifier). It MUST NOT be used for native PQ verify rows.
