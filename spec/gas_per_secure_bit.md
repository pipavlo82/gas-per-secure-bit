# Gas per secure bit — Spec v0

## Goal
Normalize EVM verification cost by the delivered security / entropy, so comparisons are meaningful across schemes and deployments.

## Definitions

### Signatures (verification)
We define:

gas_per_secure_bit = gas_verify / lambda_eff

- gas_verify: gas used by on-chain verification under a defined harness.
- lambda_eff: effective security level in bits (per threat model), e.g. 128.

### Verifiable randomness (VRF / beacon-style)
We define:

gas_per_verifiable_bit = gas_verify / H_min(output | A)

- H_min: min-entropy of the output given the adversary model A (bias/withholding/choice-space).

## Threat model profiles (initial)

TM1: "Classical-128 baseline"
- lambda_eff = 128
- Use for first-pass normalization and benchmarking discipline.

TM2: "PQ target"
- lambda_eff chosen per scheme and accepted PQ estimates.

TM3: "Bias / withholding model" (for VRF/beacons)
- Explicitly define adversary choice-space and timing.
- Report H_min assumptions clearly; do not default to 256.

## Reporting requirements (canonical row)
Each benchmark record MUST include:

- scheme (ecdsa | falcon1024 | dilithium | mldsa65 | ...)
- bench_name
- chain_profile (L1, L2, calldata model if relevant)
- gas_verify
- security_metric_type (lambda_eff | H_min)
- security_metric_value
- gas_per_secure_bit
- notes (hash/xof profile, implementation refs, commit hash, etc.)
