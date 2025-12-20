# Case Catalog (AA weakest-link / protocol envelope dominance)

This catalog defines benchmark “surface classes” used in the dataset.

## Surface classes

### L1_envelope
Protocol-level transaction envelope signature assumptions (e.g., ECDSA on L1). This is often a dominant weakest-link dependency for higher-layer authentication.

### AA_userop_auth
Account Abstraction user operation authentication surfaces (e.g., validateUserOp / wallet auth), including PQ signatures inside AA.

### ERC1271_contract_verify
EIP-1271 style contract verification paths (contract-based signature checks).

### PQ_verify_onchain
On-chain verification primitives for post-quantum signatures (e.g., ML-DSA, Falcon).

### Entropy_attestation
Entropy/VRF attestations or commitments that influence ordering/randomness/security assumptions.

### Hash_commitment
Hash-only commitment or domain separation primitives used for replay protection and binding.

## Weakest-link model
For pipelines with dependencies, define:
- security_model = weakest_link
- depends_on = [ ... ]
and compute effective_security_bits = min(security-equivalent bits over the dependency set).

## Pipelines / graphs
A “pipeline” is a named dependency graph (see `spec/case_graph.md`) that defines how records compose into an end-to-end security assumption set.
## vNext: Entropy / Attestation surface nodes (draft)

These nodes extend the case-graph model beyond signature verification into protocol envelope surfaces
(randomness, commitments, attestations). For these rows, the canonical denominator is:

- security_metric_type = `H_min`
- security_metric_value = min-entropy bits under an explicit threat model

### Canonical node IDs (vNext)
- `randao::l1_randao_mix_surface`
- `commitment::sequencer_commitment_surface`
- `attestation::relay_attestation_surface`
- `attestation::bundler_attestation_surface`
- `vrf::vrf_verify_surface`
- `entropy::beacon_oracle_surface`
## Canonical baseline nodes (vNext)

- `ecdsa::l1_envelope_assumption`
  - Purpose: model L1 transaction envelope dominance for end-to-end AA security.
  - security_metric_type: `security_equiv_bits`
  - security_metric_value: 128

- `randao::l1_randao_mix_surface`
  - Purpose: protocol entropy surface baseline (RANDAO mix), used for vNext VRF/randomness graphs.
  - security_metric_type: `H_min`
  - security_metric_value: placeholder (explicitly threat-model dependent)

- `attestation::relay_attestation_surface`
  - Purpose: protocol envelope surface baseline (relay/builder attestations), used for vNext readiness graphs.
  - security_metric_type: `H_min`
  - security_metric_value: placeholder (explicitly threat-model dependent)

### Notes
- These are intentionally modeled as separate surfaces so “PQ verify gas” is not conflated with
  protocol envelope readiness.
- Rows may start as baseline placeholders (gas_verify=0) and later be upgraded to measured benches.
