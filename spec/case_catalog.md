# Case Catalog (AA weakest-link / protocol envelope dominance)

This catalog defines benchmark "surface classes" used in the dataset.

---

## Surface Classes

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

---

## Weakest-link Model

For pipelines with dependencies, define:
- `security_model = weakest_link`
- `depends_on = [ ... ]`

and compute:

```
effective_security_bits = min( security_bits(dep_i) )
```

where `security_bits(dep)` is derived from `security_metric_type ∈ {security_equiv_bits, lambda_eff, H_min}`.

---

## Pipelines / Graphs

A "pipeline" is a named dependency graph that defines how records compose into an end-to-end security assumption set.

For concrete node IDs, baseline definitions, and canonical dependency graphs, see `spec/case_graph.md`.

---

## Notes

- Surface classes are intentionally modeled separately so "PQ verify gas" is not conflated with protocol envelope readiness.
- Records may start as baseline placeholders (`gas_verify=0`) and later be upgraded to measured benches.
- Rows should be tagged with appropriate surface class metadata to enable correct weakest-link composition.
