# Protocol Readiness Table (auto-generated)

Generated from `data/results.jsonl` using a weakest-link dependency cap model (`depends_on`).

Reproduce:
```bash
python3 scripts/make_protocol_readiness.py
```

| Category | Surface | Gas | effective_security_bits | Target (bits) | Capped by | Blocker |
|---|---|---:|---:|---:|---|---|
| attestation | `attestation::relay_attestation_surface` | 12457 | 128 | 128 | - |  |
| dilithium | `dilithium::dilithium_verify_nistkat` | 20161676 | 128 | 128 | - |  |
| dilithium | `dilithium::ethdilithium_verify_evmfriendly` | 13495423 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_erc1271_isValidSignature_foundry` | 21413 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_verify_bytes65_foundry` | 24032 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_verify_ecrecover_foundry` | 21126 | 128 | 128 | - |  |
| ecdsa | `ecdsa::l1_envelope_assumption` | 0 | 128 | 128 | - |  |
| entropy | `entropy::randao_hash_based_assumption` | 0 | 128 | 128 | - |  |
| falcon | `falcon::falcon_getUserOpHash_via_entry` | 218333 | 256 | 256 | - |  |
| falcon | `falcon::falcon_handleOps_userOp_e2e` | 10966076 | 256 | 256 | - |  |
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
| vrf_pq | `vrf_pq::pq_vrf_target_assumption` | 0 | 192 | 192 | - |  |

Notes:
- `effective_security_bits` is conservative: it never exceeds the weakest dependency in `depends_on`.
- `H_min` surfaces are currently placeholders until the threat model is finalized (gas is measured).
- `Target (bits)` is display-only: if a category is unknown, target falls back to `max(own_bits, effective_bits)`.

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
| `verify_poc_foundry` | 68,901,612 | `lambda_eff` | 128 | 538,293.84375 | `d9aabc14cf13` | sec192=192 gpb192=358,862.5625 | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle=test_verify_gas_... |
| `preA_compute_w_fromPackedA_ntt_rho0_log` | 1,499,354 | `lambda_eff` | 128 | 11,713.703125 | `d9aabc14cf13` | sec192=192 gpb192=7,809.135417 | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle=gas_compute_w_fr... |
| `preA_compute_w_fromPackedA_ntt_rho1_log` | 1,499,354 | `lambda_eff` | 128 | 11,713.703125 | `d9aabc14cf13` | sec192=192 gpb192=7,809.135417 | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle=gas_compute_w_fr... |
<!-- MLDSA65_VENDOR_END -->

<!-- FALCON_VENDOR_BEGIN -->
### Falcon vendor (QuantumAccount) — pinned ref

| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |
|---|---:|---|---:|---:|---|---|---|
| `falcon_getUserOpHash_via_entry` | 218,333 | `security_equiv_bits` | 256 | 852.86328125 | `QuantumAccount`@`1970dcad8907` | `standalone` | sec256=256 gpb256=852.86328125 |
| `falcon_handleOps_userOp_e2e` | 10,966,076 | `security_equiv_bits` | 256 | 42836.234375 | `QuantumAccount`@`1970dcad8907` | `weakest-link` | sec256=256 gpb256=42836.234375 weakest_link=erc4337_bundler_ecdsa eff128=128 gpb_eff=85672.46875 |

Notes:
- `falcon_getUserOpHash_via_entry` measures the EntryPoint hashing surface (not end-to-end AA execution).
- `falcon_handleOps_userOp_e2e` measures an end-to-end `handleOps()` flow, including ERC-4337 surface overhead; treat as a protocol-surface upper bound.
- Normalization in this repo uses `security_equiv_bits = 256` for Falcon-1024 (Cat5-style denominator).
<!-- FALCON_VENDOR_END -->

<!-- DILITHIUM_VENDOR_BEGIN -->
### Dilithium vendor (ZKNoxHQ/ETHDILITHIUM) — pinned ref

| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |
|---|---:|---|---:|---:|---|---|---|
| `dilithium_verify_nistkat` | 20,161,676 | `security_equiv_bits` | 128 | 157513.09375 | `ZKNoxHQ/ETHDILITHIUM`@`df999ed4f80` | `standalone` | sec128=128 gpb128=157513.09375 |

Notes:
- `dilithium_verify_nistkat` is the NIST-shape verifier in the vendor repo.
- `ethdilithium_verify_evmfriendly` is the EVM-friendly variant in the same vendor repo.
- Denominator here uses `security_equiv_bits` (override SEC_BITS_* in the runner if you confirm a different category).
<!-- DILITHIUM_VENDOR_END -->
