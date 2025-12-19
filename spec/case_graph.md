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
