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
Each benchmark record MAY include:

- lane_assumption (explicit_lane_v0 | implicit_or_legacy)
- wiring_lane (canonical lane id, e.g. EVM_SIG_LANE_V0 | EVM_ZK_FROM_PQ_LANE_V0)
### Optional metadata: key storage realism

Bench records MAY include `key_storage_assumption` to make off-chain key handling explicit. This is metadata (orthogonal to on-chain gas), intended to avoid mixing threat models when comparing results.

Allowed values (v0):
- `tpm_resident_signing` — private key never leaves TPM/SE/HSM; signing happens inside hardware (where supported).
- `tpm_sealed_ephemeral_use` — key is sealed/encrypted at rest under a TPM/SE/HSM-derived KEK; plaintext exists only ephemerally in process memory during signing with explicit zeroization.
- `software_exportable` — key material is software-managed / exportable; no hardware-backed isolation assumption.
- `unknown` — not specified.
### Optional metadata: explicit message lanes

Bench records MAY include explicit-lane annotations to prevent replay-by-interpretation
and to keep benchmarks comparable across verification surfaces.

Fields (v0):
- `lane_assumption`:
  - `explicit_lane_v0` — signature/verification binds a versioned lane envelope (see `spec/explicit_lanes.md`)
  - `implicit_or_legacy` — lane semantics are not explicitly bound; MUST be treated as non-comparable across surfaces
- `wiring_lane`: canonical lane identifier (e.g., `EVM_SIG_LANE_V0`)
  - SHOULD be present when `lane_assumption=explicit_lane_v0`
  - MAY be omitted for legacy/implicit schemes
