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
