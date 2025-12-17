# Gas per secure bit — grant-oriented spec (plain language, v0)

This document is the “hardened” explanation of the metric for reviewers.
It is separate from `spec/gas_per_secure_bit.md` (the more detailed / discussion-oriented spec).

---

## TL;DR

We compare EVM verification cost normalized by effective security:

**gas_per_secure_bit = gas_verify / security_bits**

Today, for signatures, `security_bits` is recorded as `lambda_eff` (effective security level in bits).
Later, for VRF/randomness, `security_bits` becomes `H_min` (min-entropy of the verified output).

---

## What the metric means

- `gas_verify`: gas used on-chain for a clearly-defined verification step (signature/proof/verified computation)
- `security_bits`:
  - **signatures**: `lambda_eff` (effective security bits; declared explicitly)
  - **VRF/randomness (future)**: `H_min` under an explicit threat model

This normalization avoids misleading comparisons that only show “gas per verify” while mixing different security levels.

---

## What MUST be reported with every result (reproducibility)

Each dataset row should include:

- `repo`, `commit` (provenance of the implementation)
- `scheme`, `bench_name`
- `chain_profile` (EVM/L1 now; extendable to L2 profiles)
- `gas_verify`
- `security_metric_type` and `security_metric_value`
  - currently: `security_metric_type = lambda_eff`
- `notes` (what exactly is measured; what is included/excluded)

---

## Current working convention for `lambda_eff` (explicit assumptions)

This repo treats `lambda_eff` as a declared field.
Current dataset uses a simple convention for benchmarking:

- **ECDSA (secp256k1)**: `lambda_eff = 128` (classical security)
- **ML-DSA-65 (FIPS-204 / Dilithium-III shape)**: `lambda_eff = 128` (post-quantum target category)
- **Falcon-1024**: `lambda_eff = 256` (post-quantum target category)

These numbers can be revised, but the key rule is: the dataset must state them explicitly.

---

## What is NOT “pure verify” (avoid bad comparisons)

Some benches measure full pipelines, not a single signature verification.
Example: EIP-4337 `EntryPoint.handleOps` includes multiple checks and execution overhead.

Rule:
- mark such benches in `notes`
- do not compare them as if they are standalone signature verification

---

## Snapshot vs statistics

Current results are **snapshot-based** (single-run measurements).
If we add repeated runs, we should report:
- `n`, `min/median/max` (or percentile stats)
- environment notes (Foundry version, EVM config)
- optional error bars in plots

---

## Why this matters (grant framing)

This project provides:
1) a normalized cost metric (gas per security bit),
2) reproducible datasets with provenance,
3) a benchmark lab to compare PQ signature candidates and VRF-style constructions on EVM.

It is intended to evolve into a shared methodology others can reuse.
