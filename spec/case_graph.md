# Case Graph (execution-path dependencies)

This document defines canonical dependency graphs (“execution paths”) used to compute weakest-link effective security.

## Node naming convention

Use `scheme::bench_name` when a node corresponds to a dataset record.
Use `baseline::<name>` for conceptual baselines.

## Baseline nodes (recommended)

- `ecdsa::l1_envelope_assumption`
  - Protocol-level L1 transaction envelope signature assumption (classical ECDSA).

## Canonical graphs

### G1 — AA / ERC-4337 end-to-end (EntryPoint.handleOps)

Represents the full user operation execution path (bundler tx → EntryPoint → account validation).

**Dependencies**
- `falcon1024::qa_handleOps_userop_foundry` (measured)
- `ecdsa::l1_envelope_assumption` (baseline)

**Weakest-link effective security**
- `min( security(falcon1024::qa_handleOps_userop_foundry), security(ecdsa::l1_envelope_assumption) )`

### G2 — AA account validation only (validateUserOp)

Represents account-level authentication without the full handleOps envelope.

**Dependencies**
- `falcon1024::qa_validateUserOp_userop_log` (measured)
- `ecdsa::l1_envelope_assumption` (baseline)

**Weakest-link effective security**
- `min( security(falcon1024::qa_validateUserOp_userop_log), security(ecdsa::l1_envelope_assumption) )`

### G3 — PQ primitive verification only (library / contract verify)

Represents pure on-chain PQ verification primitive cost, without protocol envelope assumptions.

**Dependencies**
- `falcon1024::falcon_verifySignature_log` (measured)

**Effective security**
- `security(falcon1024::falcon_verifySignature_log)`

## Notes

- These graphs are intentionally minimal: they isolate the protocol envelope dominance effect.
- Additional edges can be introduced for sequencing/randomness/attestation surfaces as the dataset expands.
## vNext: AA + protocol envelope graph (entropy / attestation surfaces)

### Canonical surfaces (summary)
- S0: Pure signature verify (verifySignature / verify())
- S1: Contract wallet interface (ERC-1271 isValidSignature)
- S2: AA validation (validateUserOp)
- S3: AA end-to-end (EntryPoint.handleOps)
- E*: Envelope / entropy / attestation surfaces (vNext)

### Canonical AA weakest-link (L1) with entropy/attestation nodes (vNext)
`AA_handleOps` depends on:
- `AA_validateUserOp`
- `ecdsa::l1_envelope_assumption` (L1 envelope)
- `randao::l1_randao_mix_surface` (entropy surface; vNext)

`AA_validateUserOp` depends on:
- wallet signature verification surface (PQ candidate, e.g. Falcon/ML-DSA)

### Weakest-link rule
For any pipeline row with `depends_on`:
- effective_security_bits = min(security_bits(dep_i))
- For entropy nodes: security_bits(dep) is `H_min` in bits.
## Canonical AA weakest-link case graph (L1, v0)

This graph is a *surface taxonomy + dependency model* used to prevent apples/oranges comparisons
and to make protocol envelope dominance explicit.

```mermaid
graph TD
  S3["S3: AA end-to-end (EntryPoint.handleOps)"]
  S2["S2: AA validation (validateUserOp)"]
  S1["S1: Contract wallet interface (ERC-1271 isValidSignature)"]
  S0["S0: Pure signature verify (verifySignature/verify only)"]

  ENV["L1 envelope signature (ECDSA today) — baseline node"]
  RANDAO["Entropy surface: RANDAO mix (H_min) — vNext baseline node"]
  RELAY["Envelope surface: relay/builder attestation (H_min) — vNext baseline node"]

  S3 --> S2
  S2 --> S1
  S1 --> S0

  S3 --> ENV

  %% vNext envelope/entropy surfaces (optional dependencies)
  S3 -.-> RANDAO
  S3 -.-> RELAY
Effective security rule

For any pipeline node with depends_on[]:

effective_security_bits = min(security_bits(dep_i))

Where security_bits(x) is derived from records with
security_metric_type ∈ {security_equiv_bits, lambda_eff, H_min}.

Interpretation (L1): even if the wallet signature is PQ (e.g., 256), end-to-end AA can still be bounded by the L1 envelope (e.g., 128).
