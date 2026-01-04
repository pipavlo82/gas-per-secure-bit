# Protocol Readiness Table (auto-generated)

Generated from `data/results.jsonl` using a weakest-link dependency cap model (`depends_on`).

Reproduce:
```bash
python3 scripts/make_protocol_readiness.py
```

| Category | Surface | Gas | effective_security_bits | Target (bits) | Capped by | Blocker |
|---|---|---:|---:|---:|---|---|
| attestation | `attestation::relay_attestation_surface` | 43876 | 128 | 128 | - |  |
| das | `das::verify_sample_512b_surface` | 2464 | 4096 | 128 | - |  |
| dilithium | `dilithium::dilithium_verify_nistkat` | 20161676 | 128 | 128 | - |  |
| dilithium | `dilithium::ethdilithium_verify_evmfriendly` | 13495423 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_erc1271_isValidSignature_foundry` | 21413 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_verify_bytes65_foundry` | 24032 | 128 | 128 | - |  |
| ecdsa | `ecdsa::ecdsa_verify_ecrecover_foundry` | 21126 | 128 | 128 | - |  |
| ecdsa | `ecdsa::l1_envelope_assumption` | 0 | 128 | 128 | - |  |
| entropy | `entropy::randao_hash_based_assumption` | 0 | 128 | 128 | - |  |
| falcon | `falcon::falcon_getUserOpHash_via_entry` | 218333 | 256 | 256 | - |  |
| falcon | `falcon::falcon_handleOps_userOp_e2e` | 10966076 | 128 | 256 | ecdsa::l1_envelope_assumption | Capped by L1 ECDSA envelope assumption (PQ not enshrined end-to-end). |
| falcon | `falcon::falcon_verifySignature_log` | 10336055 | 256 | 256 | - |  |
| falcon | `falcon::qa_validateUserOp_userop_log` | 10589132 | 256 | 256 | - |  |
| mldsa65 | `mldsa65::preA_compute_w_fromPackedA_ntt_rho0_log` | 1499354 | 128 | 192 | - |  |
| mldsa65 | `mldsa65::preA_compute_w_fromPackedA_ntt_rho1_log` | 1499354 | 128 | 192 | - |  |
| mldsa65 | `mldsa65::verify_poc_foundry` | 68901612 | 128 | 192 | - |  |
| randao | `randao::l1_randao_mix_surface` | 5820 | 32 | 128 | - |  |
| randao | `randao::mix_for_sample_selection_surface` | 13081 | 32 | 128 | - |  |
| vrf_pq | `vrf_pq::pq_vrf_target_assumption` | 0 | 192 | 192 | - |  |

Notes:
- `effective_security_bits` is conservative: it never exceeds the weakest dependency in `depends_on`.
- `H_min` surfaces are currently placeholders until the threat model is finalized (gas is measured).
- `Target (bits)` is display-only: if a category is unknown, target falls back to `max(own_bits, effective_bits)`.

<!-- MLDSA65_VENDOR_BEGIN -->
## ML-DSA-65 (vendor / pinned ref) — measured points

These rows are produced by `scripts/run_vendor_mldsa.sh` and currently require pinning `MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA` because upstream `main` does not contain the gas harness tests (`test_verify_gas_poc`, `PreA_ComputeW_GasMicro`) yet.

Note: the dataset currently records ML-DSA-65 rows with `security_metric_type=lambda_eff` and `value=128`. To avoid rewriting later, the table keeps that denominator, and `notes` additionally reports `security_equiv_bits=192` and `gas/bit@192` (= gas_verify/192).

Vector pack (shared reference for these measurements):
- `vector_pack_ref`: `pipavlo82/pqevm-vector-packs@05988be4f37394b21257d2b5e6c639b4746b698a:packs/mldsa65_fips204`
- `vector_pack_id`: `5d3e99cb335072a30391f08655398b590634897d953a97d539a6c8e2d20183ed`
- `vector_id`: `mldsa65_fips204_vector_001`

Reproduce:

```bash
export MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA
bash scripts/run_vendor_mldsa.sh
bash scripts/make_reports.sh
```

| bench | gas_verify | denom | value | gas/bit | vendor commit | notes |
|---|---:|---|---:|---:|---|---|
| `verify_poc_foundry` | 68,901,612 | `lambda_eff` | 128.0 | 538293.84375 | `d9aabc14cf13` | sec192=192 gpb192=358,862.5625 | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle... |
| `preA_compute_w_fromPackedA_ntt_rho0_log` | 1,499,354 | `lambda_eff` | 128.0 | 11713.703125 | `d9aabc14cf13` | sec192=192 gpb192=7,809.135417 | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle... |
| `preA_compute_w_fromPackedA_ntt_rho1_log` | 1,499,354 | `lambda_eff` | 128.0 | 11713.703125 | `d9aabc14cf13` | sec192=192 gpb192=7,809.135417 | ml-dsa-65-ethereum-verification (ref=feature/mldsa-ntt-opt-phase12-erc7913-packedA; needle... |
<!-- MLDSA65_VENDOR_END -->

<!-- FALCON_VENDOR_BEGIN -->
### Falcon vendor (QuantumAccount) — pinned ref

| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |
|---|---:|---|---:|---:|---|---|---|
| `falcon_verifySignature_log` | 10,336,055 | `security_equiv_bits` | 256 | 40375.21484375 | `QuantumAccount`@`1970dcad890` | `raw` | log-isolated; Foundry logs: test_falcon_verify_gas_log => 'gas_falcon_verify: <N>' |
| `qa_validateUserOp_userop_log` | 10,589,132 | `security_equiv_bits` | 256 | 41363.796875 | `QuantumAccount`@`1970dcad890` | `raw` | log-isolated; Foundry logs: test_validateUserOp_gas_log => 'gas_validateUserOp: <N>' |
| `falcon_getUserOpHash_via_entry` | 218,333 | `security_equiv_bits` | 256 | 852.86328125 | `QuantumAccount`@`1970dcad890` | `standalone` | AA surface: EntryPoint hashing only (not end-to-end AA execution) |
| `falcon_handleOps_userOp_e2e` | 10,966,076 | `security_equiv_bits` | 256 | 42836.234375 | `QuantumAccount`@`1970dcad890` | `weakest-link` | end-to-end AA (`handleOps`); treat as protocol-surface upper bound; weakest-link=ecdsa::l1_envelope_assumption eff128=128 gpb_eff=85672.46875 |

Notes:
- Vendor is pinned by commit in dataset: `QuantumAccount`@`1970dcad890`.
- `security_equiv_bits = 256` is used as the Falcon-1024 normalization denominator in this repo.
<!-- FALCON_VENDOR_END -->

<!-- DILITHIUM_VENDOR_BEGIN -->
### Dilithium vendor (ZKNoxHQ/ETHDILITHIUM) — pinned ref

| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |
|---|---:|---|---:|---:|---|---|---|
| `dilithium_verify_nistkat` | 20,161,676 | `security_equiv_bits` | 128 | 157513.09375 | `ZKNoxHQ/ETHDILITHIUM`@`df999ed4f80` | `standalone` | sec128=128 gpb128=157513.09375; path-pinned; Foundry: test/ZKNOX_dilithiumKATS.t.sol:testVerify |
| `ethdilithium_verify_evmfriendly` | 13,495,423 | `security_equiv_bits` | 128 | 105432.9921875 | `ZKNoxHQ/ETHDILITHIUM`@`df999ed4f80` | `standalone` | sec128=128 gpb128=105432.9921875; path-pinned; Foundry: test/ZKNOX_ethdilithiumKAT.t.sol:testVerify |

Notes:
- Vendor is pinned by commit in dataset: `ZKNoxHQ/ETHDILITHIUM`@`df999ed4f80`.
- `dilithium_verify_nistkat` is the NIST-shape verifier in the vendor repo.
- `ethdilithium_verify_evmfriendly` is the EVM-friendly variant in the same vendor repo.
- Recorded points are signature verification only (sig::verify); AA end-to-end surfaces (validateUserOp/handleOps) are not yet measured for this vendor.
- Denominator here uses `security_equiv_bits` (override SEC_BITS_* in the runner if you confirm a different category).
<!-- DILITHIUM_VENDOR_END -->
