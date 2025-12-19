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
