# Security metrics & denominators

This repo uses *declared denominators* to normalize gas costs across schemes and surfaces.
These denominators are **conventions for comparability**, not proofs about a specific Solidity implementation.

## 1) `security_equiv_bits` (signatures)

For signature benchmarks we use:

- `security_metric_type = "security_equiv_bits"`
- `gas_per_secure_bit = gas / security_equiv_bits`

`security_equiv_bits` is a **classical-equivalent security level** chosen as a *declarative* mapping
(e.g., NIST PQC categories) so that datasets are comparable across algorithms.

### Convention table (default)
| Category / baseline | `security_equiv_bits` | Notes |
|---|---:|---|
| Classical baseline (ECDSA/SECP256K1 budgeting) | 128 | Used for "budgeting" comparisons |
| NIST Cat 1 | 128 | Conservative classical-equivalent |
| NIST Cat 3 | 192 | Conservative classical-equivalent |
| NIST Cat 5 | 256 | Conservative classical-equivalent |

### Important disclaimers
- This value **does not claim** a specific implementation achieves the stated security.
- It **does not model** side-channels, fault attacks, compiler bugs, or protocol misuse.
- It **only** provides a consistent denominator for ecosystem-scale comparisons.

When the community converges on better normalization (e.g., λ_eff under a specific cost model),
we can add `security_metric_type = "lambda_eff"` in a backward-compatible way.

## 2) `H_min` (entropy / randomness surfaces)

For protocol surfaces (RANDAO, attestation relay, DAS sampling, etc.), the denominator should be
`H_min` (min-entropy) **under an explicit threat model**.

At early stages we may record `H_min` as a placeholder while the threat model is being finalized.
The dataset must always mark what metric is used via `security_metric_type`.

## 3) Composition (weakest-link)

For composite systems we use a weakest-link rule:

effective_security_bits = min(security_bits(dep_i))

This prevents overstating PQ readiness when a PQ primitive is wrapped by a weaker legacy surface.
