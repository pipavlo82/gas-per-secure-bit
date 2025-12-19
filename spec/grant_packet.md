# Grant packet: Gas per Secure Bit + Protocol Readiness Surfaces

## Project summary (1–2 sentences)
This project standardizes a **normalized benchmark** for post-quantum (PQ) verification on EVM using **gas per secure bit**, and extends it with a **dataset-backed weakest-link model** to capture protocol envelope dominance and future entropy/attestation surfaces.

## Problem
EVM PQ discussions typically compare “gas per verify” while mixing:
- different security levels (128/192/256),
- different execution paths (EOA vs AA/ERC-4337 vs ERC-1271),
- and hidden protocol dependencies (e.g., L1 transaction envelope signatures).

This prevents engineering-grade answers to “is scheme X viable on EVM?” and obscures where end-to-end PQ readiness is actually blocked.

## Approach
1. **Dataset-first benchmarking**
   - Canonical JSONL dataset with provenance (`repo`, `commit`) and normalization fields.
2. **Normalization**
   - `gas_per_secure_bit = gas_verify / security_equiv_bits` (signatures)
   - vNext for randomness/VRF: `security_metric_type = H_min` (min-entropy bits) under an explicit threat model.
3. **Weakest-link composition**
   - Pipelines defined via `depends_on`.
   - Effective security computed as the minimum security across dependencies.

## Current deliverables (already implemented)
- Weakest-link report (dataset-backed):
  - `reports/weakest_link_report.md`
  - Demonstrates envelope dominance: AA PQ wallet (256) → effective 128 when the L1 envelope is ECDSA.
- Protocol readiness report:
  - `reports/protocol_readiness.md`
  - Summarizes weakest-link surfaces and the vNext entropy/attestation modeling direction.
- Specification and schema:
  - `spec/gas_per_secure_bit_for_grants.md`
  - `spec/pqsig_userop_schema_v0.1.md`
  - `spec/case_graph.md` and `spec/case_catalog.md`

## Milestones (proposed)
### M1 — Dataset hardening + reference pipelines
- Add canonical pipeline graphs:
  - ERC-4337 handleOps end-to-end, validateUserOp-only, ERC-1271 contract verification.
- Add optional dedup tooling to keep the latest record per `(scheme, bench_name, repo, commit)`.

### M2 — Vendor benchmark expansion (PQ signatures)
- Add reproducible vendor runners for:
  - Falcon (AA / ERC-4337),
  - ML-DSA / Dilithium variants (verification primitives and AA paths where available),
  - and at least one additional PQ scheme if feasible.
- Ensure each entry includes provenance and comparable chain profiles.

### M3 — Entropy / attestation surfaces (vNext)
- Add first concrete entropy/attestation benchmark(s):
  - at least one on-chain verification cost for an entropy/VRF-like proof, if available,
  - otherwise formalize placeholder nodes and document assumptions rigorously.

### M4 — Publication + community review
- Publish a short technical note (README + report links) explaining:
  - why “weakest-link” matters,
  - how to reproduce numbers,
  - how to contribute new benchmarks.

## Why this matters (impact)
- Provides a **single normalized unit** for PQ verification on EVM.
- Turns PQ readiness discussions into **measurable bottlenecks** (dataset-backed).
- Creates a reusable dataset + methodology to track progress as protocol-level features evolve.

## Repo pointers
- Grant-oriented spec: `spec/gas_per_secure_bit_for_grants.md`
- Weakest-link analysis: `reports/weakest_link_report.md`
- Protocol readiness summary: `reports/protocol_readiness.md`
