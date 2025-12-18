# Gas per Secure Bit — Grant-Oriented Spec (Plain Language, v0)

> **Note:** This document is the "hardened" explanation of the metric for reviewers. It is separate from `spec/gas_per_secure_bit.md` (the more detailed / discussion-oriented spec).

---

## TL;DR

We compare EVM verification cost normalized by an explicit security target:

```
gas_per_secure_bit = gas_verify / security_equiv_bits
```

Where `security_equiv_bits` is a declared "classical-equivalent bits" convention for fair normalization.

Later, for VRF/randomness, `security_equiv_bits` can be replaced by `H_min` (min-entropy) under an explicit threat model:

```
gas_per_entropy_bit = gas_verify / H_min
```

---

## What the Metric Means

**`gas_verify`:** Gas used on-chain for a clearly-defined verification step (signature/proof/verified computation).

**`security_equiv_bits`:** For signatures, a declared "classical-equivalent bits" value used for normalization (e.g., 128 / 192 / 256). For VRF/randomness (future), use `H_min` under an explicit threat model.

**Why this matters:** This avoids misleading comparisons that only show "gas per verify" while mixing different security levels.

---

## What MUST Be Reported with Every Result (Reproducibility)

Each dataset row should include:

- **`repo`, `commit`:** Provenance of the implementation
- **`scheme`, `bench_name`:** What is being measured
- **`chain_profile`:** EVM/L1 now; extendable to L2 profiles
- **`gas_verify`:** Gas cost measurement
- **`security_metric_type` and `security_metric_value`:**
  - Recommended for signatures: `security_metric_type = security_equiv_bits`
  - Recommended for randomness: `security_metric_type = H_min`
- **`notes`:** What exactly is measured; what is included/excluded

---

## Security Reporting for Signatures (Explicit Assumptions)

This repo separates two ideas:

1. **Security category:** NIST PQ categories, where applicable (1 / 3 / 5)
2. **Security-equivalent bits:** Used for normalization (`security_equiv_bits`)

### Current Working Convention (Signatures)

The dataset must declare `security_equiv_bits` explicitly. A reasonable default convention is:

| Scheme | Security Category | `security_equiv_bits` | Notes |
|--------|-------------------|----------------------|-------|
| **ECDSA (secp256k1)** | - | 128 | Classical security convention |
| **ML-DSA-65 (FIPS-204)** | 3 | 192 | Classical-equivalent convention |
| **Falcon-1024** | 5 | 256 | Classical-equivalent convention |

**Note:** These "equivalent bits" are a normalization convention, not a proof statement. The key rule is that they are explicit and consistent across comparisons.

---

## Optional Baseline Normalization (Separate Metric)

If we want a simple baseline comparison (e.g., "per 128-bit baseline"), we compute:

```
gas_per_128b = gas_verify / 128
```

**Important:** This is not a claim that ML-DSA-65 is "128-bit secure"; it is a baseline normalization only.

---

## What is NOT "Pure Verify" (Avoid Bad Comparisons)

Some benches measure full pipelines, not a single signature verification.

**Example:** EIP-4337 `EntryPoint.handleOps` includes multiple checks and execution overhead.

**Rule:** Mark such benches in `notes`; do not compare them as if they are standalone signature verification.

---

## Snapshot vs Statistics

**Current results are snapshot-based** (single-run measurements).

If we add repeated runs, we should report:

- `n`, `min/median/max` (or percentile stats)
- Environment notes (Foundry version, EVM config)
- Optional error bars in plots

---

## Why This Matters (Grant Framing)

This project provides:

1. **A normalized cost metric** (`gas per security bit` / `gas per entropy bit`)
2. **Reproducible datasets** with provenance
3. **A benchmark lab** to compare PQ signature candidates and VRF-style constructions on EVM

It is intended to evolve into a shared methodology others can reuse.

