# Protocol readiness: weakest-link surfaces (dataset-backed)

This report summarizes where post-quantum (PQ) security assumptions can be bottlenecked by classical components, using dataset records and weakest-link composition.

## 1) Envelope dominance (L1 transaction signature)

Even if an AA wallet uses a PQ signature scheme, end-to-end security can remain bounded by the protocol envelope signature that carries the transaction on L1.

**Dataset nodes**
- Baseline: `ecdsa::l1_envelope_assumption` (declared 128-bit equivalent)
- AA pipelines (measured): `falcon1024::qa_handleOps_userop_foundry`, `falcon1024::qa_validateUserOp_userop_log`
- Derived weakest-link views:
  - `falcon1024::qa_handleOps_userop_foundry_weakest_link`
  - `falcon1024::qa_validateUserOp_userop_log_weakest_link`

**Key result**
- In weakest-link composition, `effective_security_bits = min(256, 128) = 128`.
- This formalizes the “PQ inside AA does not automatically upgrade the whole system” statement in a measurable way.

## 2) Entropy / ordering / attestation surfaces (vNext)

Separately from signature authentication, protocol-level security depends on randomness, ordering, and attestations (L2 / committees / relays).

This repo models those as benchmark nodes using:
- `security_metric_type = H_min` (min-entropy bits) under an explicit `threat_model`
- `surface_class`, `entropy_source`, `attestation_surface`

**Baseline target nodes added**
- `entropy::randao_hash_based_assumption` (H_min, declared)
- `vrf_pq::pq_vrf_target_assumption` (H_min, declared)

These are placeholders until concrete on-chain verification costs and conformance tests are added.

## 3) What changes end-to-end outcomes

To move the bottleneck, a PQ-ready stack must address:
1. Protocol envelope signature surface (L1)
2. AA verification surface (account / EntryPoint)
3. Entropy / VRF attestation surface
4. L2 attestation aggregation surface (where applicable)

This dataset and graph methodology provides a standardized way to track progress across those surfaces.

## References within this repo

- Case catalog: `spec/case_catalog.md`
- Case graphs: `spec/case_graph.md`
- Weakest-link report: `reports/weakest_link_report.md`
- Entropy surfaces note: `reports/entropy_surface_notes.md`
