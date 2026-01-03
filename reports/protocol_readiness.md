# Protocol Readiness Table (auto-generated)

Generated from `data/results.jsonl` using a weakest-link dependency cap model (`depends_on`).

Reproduce:
```bash
python3 scripts/make_protocol_readiness.py
```

| Category | Surface | Gas | effective_security_bits | Target (bits) | Capped by | Blocker |
|---|---|---:|---:|---:|---|---|
| attestation | `attestation::relay_attestation_surface` | 12457 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_erc1271_isValidSignature_foundry` | 21413 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_verify_bytes65_foundry` | 24032 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_verify_ecrecover_foundry` | 21126 | 128 | 128 | - |  |
| ecdsa | `ecdsa::l1_envelope_assumption` | 0 | 128 | 128 | - |  |
| entropy | `entropy::randao_hash_based_assumption` | 0 | 128 | 0 | - |  |
| falcon1024 | `falcon1024::falcon_verifySignature_log` | 10336055 | 256 | 256 | - |  |
| falcon1024 | `falcon1024::qa_getUserOpHash_foundry` | 218333 | 256 | 256 | - |  |
| falcon1024 | `falcon1024::qa_handleOps_userop_foundry` | 10966076 | 256 | 256 | - |  |
| falcon1024 | `falcon1024::qa_handleOps_userop_foundry_weakest_link` | 10966076 | 128 | 256 | ecdsa::l1_envelope_assumption | Capped by L1 ECDSA envelope assumption (PQ not enshrined end-to-end). |
| falcon1024 | `falcon1024::qa_handleOps_userop_foundry_weakest_link_vnext` | 10966076 | 32 | 256 | randao::l1_randao_mix_surface | Measured gas; H_min denominator is a placeholder until threat model is fixed. |
| falcon1024 | `falcon1024::qa_validateUserOp_userop_log` | 10589132 | 256 | 256 | - |  |
| falcon1024 | `falcon1024::qa_validateUserOp_userop_log_weakest_link` | 10589132 | 128 | 256 | ecdsa::l1_envelope_assumption | Capped by L1 ECDSA envelope assumption (PQ not enshrined end-to-end). |
| mldsa65 | `mldsa65::preA_compute_w_fromPackedA_ntt_rho0_log` | 1499354 | 128 | 192 | - |  |
| mldsa65 | `mldsa65::preA_compute_w_fromPackedA_ntt_rho1_log` | 1499354 | 128 | 192 | - |  |
| mldsa65 | `mldsa65::verify_poc_foundry` | 68901612 | 128 | 192 | - |  |
| randao | `randao::l1_randao_mix_surface` | 5993 | 32 | 128 | - |  |
| vrf_pq | `vrf_pq::pq_vrf_target_assumption` | 0 | 192 | 0 | - |  |

Notes:
- `effective_security_bits` is conservative: it never exceeds the weakest dependency in `depends_on`.
- `H_min` surfaces are currently placeholders until the threat model is finalized (gas is measured).

<!-- MLDSA65_VENDOR_BEGIN -->
## ML-DSA-65 (vendor / pinned ref) — measured points

These rows are produced by `scripts/run_vendor_mldsa.sh` and currently require pinning `MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA` because upstream `main` does not contain the gas harness tests (`test_verify_gas_poc`, `PreA_ComputeW_GasMicro`) yet.

Note: the dataset currently records ML-DSA-65 rows with `security_metric_type=lambda_eff` and `value=128`. To avoid rewriting later, the table keeps that denominator, and `notes` additionally reports `security_equiv_bits=192` and `gas/bit@192` (= gas_verify/192).

Reproduce:

```bash
export MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA
bash scripts/run_vendor_mldsa.sh
bash scripts/make_reports.sh
```

| bench | gas_verify | denom | value | gas/bit | vendor commit | notes |
|---|---:|---|---:|---:|---|---|
| `verify_poc_foundry` | 68,901,612 | `lambda_eff` | 128 | 538,293.84375 | `d9aabc14cf13` | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle=test_verify_gas_poc) | sec... |
| `preA_compute_w_fromPackedA_ntt_rho0_log` | 1,499,354 | `lambda_eff` | 128 | 11,713.703125 | `d9aabc14cf13` | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle=gas_compute_w_fromPacked_A... |
| `preA_compute_w_fromPackedA_ntt_rho1_log` | 1,499,354 | `lambda_eff` | 128 | 11,713.703125 | `d9aabc14cf13` | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle=gas_compute_w_fromPacked_A... |
<!-- MLDSA65_VENDOR_END -->
