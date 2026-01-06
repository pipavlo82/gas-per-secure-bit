# Protocol Readiness Table (auto-generated)

Generated from `data/results.jsonl` using a weakest-link dependency cap model (`depends_on`).

Reproduce:
```bash
python3 scripts/make_protocol_readiness.py
```

| Category | Surface | Gas | effective_security_bits | Target (bits) | Verified | Capped by | Blocker |
|---|---|---:|---:|---:|---|---|---|
| attestation | `attestation::relay_attestation_surface` | 43876 | 128 | 128 | - | - |  |
| das | `das::verify_sample_512b_surface` | 2464 | 4096 | 128 | - | - |  |
| dilithium | `dilithium::dilithium_verify_nistkat` | 20161676 | 128 | 128 | - | - |  |
| dilithium | `dilithium::ethdilithium_eth_verify_log` | 13493048 | 128 | 128 | - | - |  |
| dilithium | `dilithium::ethdilithium_nist_verify_log` | 20155935 | 128 | 128 | - | - |  |
| dilithium | `dilithium::ethdilithium_verify_evmfriendly` | 13495423 | 128 | 128 | - | - |  |
| ecdsa | `ecdsa::ecdsa_erc1271_isValidSignature_foundry` | 21413 | 128 | 128 | - | - |  |
| ecdsa | `ecdsa::ecdsa_verify_bytes65_foundry` | 24032 | 128 | 128 | - | - |  |
| ecdsa | `ecdsa::ecdsa_verify_ecrecover_foundry` | 21126 | 128 | 128 | - | - |  |
| ecdsa | `ecdsa::l1_envelope_assumption` | 0 | 128 | 128 | - | - |  |
| entropy | `entropy::randao_hash_based_assumption` | 0 | 128 | 128 | - | - |  |
| falcon | `falcon::falcon_getUserOpHash_via_entry` | 218333 | 256 | 256 | - | - |  |
| falcon | `falcon::falcon_handleOps_userOp_e2e` | 10966076 | 128 | 256 | - | ecdsa::l1_envelope_assumption | Capped by L1 ECDSA envelope assumption (PQ not enshrined end-to-end). |
| falcon | `falcon::falcon_verifySignature_log` | 10336055 | 256 | 256 | - | - |  |
| falcon | `falcon::qa_validateUserOp_userop_log` | 10589132 | 256 | 256 | - | - |  |
| mldsa65 | `mldsa65::preA_compute_w_fromPackedA_ntt_rho0_log` | 1499354 | 128 | 192 | ✅ tx=0xa885b619… ctr=0xe7f1725e… artifact=run-latest.json | - |  |
| mldsa65 | `mldsa65::preA_compute_w_fromPackedA_ntt_rho1_log` | 1499354 | 128 | 192 | ✅ tx=0xa885b619… ctr=0xe7f1725e… artifact=run-latest.json | - |  |
| mldsa65 | `mldsa65::verify_poc_foundry` | 68901612 | 128 | 192 | - | - |  |
| p256 | `p256::ethdilithium_p256verify_log` | 22124 | 128 | 128 | - | - |  |
| randao | `randao::l1_randao_mix_surface` | 5820 | 32 | 128 | - | - |  |
| randao | `randao::mix_for_sample_selection_surface` | 13081 | 32 | 128 | - | - |  |
| vrf_pq | `vrf_pq::pq_vrf_target_assumption` | 0 | 192 | 192 | - | - |  |

Notes:
- `effective_security_bits` is conservative: it never exceeds the weakest dependency in `depends_on`.
- `H_min` surfaces are currently placeholders until the threat model is finalized (gas is measured).
- `Target (bits)` is display-only: if a category is unknown, target falls back to `max(own_bits, effective_bits)`.
- `Verified` is ✅ only when the dataset row includes an `onchain_proof` bundle.

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
| `preA_compute_w_fromPackedA_ntt_rho0_log` | 1,499,354 | `lambda_eff` | 128.0 | 11713.703125 | `d9aabc14cf13` | sec192=192 gpb192=7,809.135417 | ✅ tx=0xa885b619… ctr=0xe7f1725e… artifact=run-latest.json ml-dsa-65-ethereum-verification ... |
| `preA_compute_w_fromPackedA_ntt_rho1_log` | 1,499,354 | `lambda_eff` | 128.0 | 11713.703125 | `d9aabc14cf13` | sec192=192 gpb192=7,809.135417 | ✅ tx=0xa885b619… ctr=0xe7f1725e… artifact=run-latest.json ml-dsa-65-ethereum-verification ... |
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


<!-- ETHDILITHIUM_VENDOR_BEGIN -->

### Vendor snapshot: ZKNoxHQ/ETHDILITHIUM

- Source: `ZKNoxHQ/ETHDILITHIUM` (pinned by commit)
- Runner: `scripts/run_vendor_ethdilithium.sh` (log-extracted `Gas used:`; excludes FFI-based tests like `testVerifyShorter()`)

| bench_name | scheme | description | gas_verify | security_metric | value | gas/bit | vendor_commit | vendor_path | notes |
|---|---:|---|---:|---|---:|---:|---|---|---|
| `ethdilithium_eth_verify_log` | `dilithium` | verify (ETH mode, log) | 13,493,048 | `lambda_eff` | 128 | 105414.4375 | `df999ed4f803` | `vendors/ETHDILITHIUM` | ETHDILITHIUM (ETH mode) (ref=df999ed4f8032d26d9d3d22748407afbb7978ae7; path=test/ZKNOX_ethdilithium.t.sol; ... |
| `ethdilithium_nist_verify_log` | `dilithium` | verify (NIST mode, log) | 20,155,935 | `lambda_eff` | 128 | 157468.242188 | `df999ed4f803` | `vendors/ETHDILITHIUM` | ETHDILITHIUM (NIST mode) (ref=df999ed4f8032d26d9d3d22748407afbb7978ae7; path=test/ZKNOX_dilithium.t.sol; ma... |
| `ethdilithium_p256verify_log` | `p256` | P-256 verify micro (log) | 22,124 | `lambda_eff` | 128 | 172.84375 | `df999ed4f803` | `vendors/ETHDILITHIUM` | ETHDILITHIUM P-256 verify micro (ref=df999ed4f8032d26d9d3d22748407afbb7978ae7; path=test/ZKNOX_p256verify.t... |

Notes:
- `lambda_eff=128` here is a budgeting denominator (not a finalized security-equivalence mapping for Dilithium variants).
- If/when we normalize Dilithium to `security_equiv_bits`, we will add `secXXX=...` and `gpbXXX=...` annotations similar to MLDSA65.

<!-- ETHDILITHIUM_VENDOR_END -->
