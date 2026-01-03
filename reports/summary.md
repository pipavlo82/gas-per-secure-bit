# Summary Report (Dataset + Methodology + Findings)

Generated artifacts in this repo:
- `data/results.jsonl` (source of truth)
- `data/results.csv` (derived table)
- `reports/weakest_link_report.md` (computed)
- `reports/entropy_surface_notes.md` (notes / framing)
- `reports/protocol_readiness.md` (human-written summary)

---
## Executive summary (what exists today)

A) **Dataset + normalized metric**  
- `data/results.jsonl` → `data/results.csv` with explicit provenance and denominators.  
- Primary signature normalization: `gas_per_secure_bit = gas_verify / security_equiv_bits`.

B) **Weakest-link / protocol envelope dominance**  
- `reports/weakest_link_report.md` computes `effective_security_bits = min(dep_i)` from `depends_on[]`.  
- Supports `{security_equiv_bits, lambda_eff, H_min}` so it can extend from signatures → entropy surfaces.

C) **Standardized case graph (surface taxonomy)**  
- `spec/case_graph.md` defines canonical surfaces S0–S3 and L1 envelope + vNext entropy/attestation nodes.  
- Goal: stop mixing scopes (microbench vs AA pipeline) and make readiness blockers measurable.

Note: protocol surfaces are now measured via Foundry harness tests and updated deterministically via `scripts/run_protocol_surfaces.sh` (the runner prunes old surface records and appends fresh measured records, then regenerates reports).


## TL;DR

- We now have a **reproducible PQ-on-EVM benchmark lab** with **explicit provenance** (`repo`, `commit`) and **explicit security denominators**.
- We added a **weakest-link composition model** for AA / protocol pipelines: if your AA wallet uses a PQ signature, the **effective security can still be capped by the L1 envelope** until the protocol de-enshrines ECDSA-style assumptions.
- We also started modeling **entropy + attestation surfaces** as first-class benchmark nodes (vNext fields), so we can extend from "signatures" to "protocol readiness" and eventually VRF / randomness.

---

## What We Have (as of current main)

### 1) Dataset + normalization (core)

**Metric:**
Normalization: `gas_per_secure_bit = gas_verify / security_metric_value`, where `security_metric_type ∈ {security_equiv_bits, lambda_eff, H_min}`.

For signatures today:
- `security_metric_type = security_equiv_bits` (declared convention; explicit in dataset)

For VRF / randomness (vNext direction):
- `security_metric_type = H_min` (min-entropy in bits) under explicit threat model (not yet populated with real VRF rows; schema supports it)

**Provenance:**
- Every row records `repo` and `commit` (override-friendly so vendor runners can record upstream provenance correctly)

**Schema:**
- `spec/pqsig_userop_schema_v0.1.md`
- `spec/pqsig_userop_schema_v0.1.example.json`
- vNext optional fields to describe surfaces and composition (see below)

---

### 2) Weakest-link composition (AA / protocol envelope dominance)

We introduced a dataset-backed composition rule:

- A pipeline record can declare `depends_on: [ "scheme::bench", ... ]`
- Effective security is:
  - `effective_security_bits = min(bits(dep_i))`

This is the critical missing piece in many PQ/AA discussions: **the strongest primitive does not determine end-to-end security if the pipeline still depends on a weaker envelope**.

**Output:**
- `reports/weakest_link_report.md`

Current derived examples:
- `falcon1024::qa_handleOps_userop_foundry_weakest_link`
- `falcon1024::qa_validateUserOp_userop_log_weakest_link`

Both show **declared 256-bit** (Falcon) becoming **effective 128-bit** when the pipeline depends on:
- `ecdsa::l1_envelope_assumption` (baseline node)

---

### 3) Entropy + attestation surfaces (vNext fields)

We extended the schema (optional fields) to start tracking:
- `surface_class` (e.g., signature-only microbench vs AA validation vs full pipeline vs envelope)
- `security_model` (e.g., `raw` vs `weakest_link`)
- `depends_on` edges (composition)
- (notes + planned) entropy/attestation descriptors to later map where PQ readiness is blocked

**Notes:**
- `reports/entropy_surface_notes.md`

---

### 4) Protocol readiness summary

We consolidated the above into a readable "protocol readiness" view:
- `reports/protocol_readiness.md`

This is *not* a new benchmark; it is a structured summary of what the dataset + weakest-link model implies about end-to-end PQ readiness.

---
---

## Latest measured points (selected)

Concrete datapoints currently present in `data/results.jsonl` (source of truth).

### ML-DSA-65 (FIPS-204 shape) — vendor bench (Foundry)

Recorded from vendored `pipavlo82/ml-dsa-65-ethereum-verification` at:
- ref: `feature/mldsa-ntt-opt-phase12-erc7913-packedA`
- commit: `d9aabc14cf13fc227c46d06cdaef17f74b069790`

Numbers (EVM/L1):
- `mldsa65::verify_poc_foundry` → gas_verify = 68,901,612; gas_per_secure_bit (lambda_eff=128) = 538,293.84375
- `mldsa65::preA_compute_w_fromPackedA_ntt_rho0_log` → gas_verify = 1,499,354; gas_per_secure_bit = 11,713.703125
- `mldsa65::preA_compute_w_fromPackedA_ntt_rho1_log` → gas_verify = 1,499,354; gas_per_secure_bit = 11,713.703125

Note: vendor `main` may not contain the gas harness tests (`test_verify_gas_poc`, `PreA_ComputeW_GasMicro`).
Until merged upstream, pin the ref explicitly.

### Reproduce the ML-DSA-65 vendor points

From repo root:

```bash
export MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA
bash scripts/run_vendor_mldsa.sh
bash scripts/make_reports.sh

## Current Dataset Coverage (high level)

### Schemes included
- **ECDSA (secp256k1)**: `ecrecover`, bytes65 wrapper, ERC-1271 `isValidSignature`
- **Falcon-1024 (QuantumAccount)**: AA-related benches + clean verifySignature microbench (log-based)
- **ML-DSA-65 (FIPS-204 shape)**: verify POC + PreA packed-A compute path microbench

### Surface classes (conceptually)
- Signature-only microbenches (pure verify)
- Contract wallet verify (ERC-1271)
- AA validation surfaces (validateUserOp-like)
- AA end-to-end path (handleOps)
- Baseline "envelope assumption" node (for weakest-link composition)

---

## How to Reproduce Reports

From repo root:

```bash
./scripts/make_reports.sh
```

This performs:

- JSONL sanity (one JSON per line)
- Uniqueness sanity for (scheme, bench_name, repo, commit)
- Regenerates:
  - `reports/weakest_link_report.md`
  - (protocol report is currently a static markdown file)

---

## Key Takeaways (what is actually new here)

### Comparability

"Gas per verify" comparisons are often invalid across different security levels and different surfaces.

We force comparability by explicitly recording:
- security denominator,
- surface class,
- and scope (microbench vs pipeline).

### Composition

PQ wallet signatures in AA do not automatically make the system PQ-ready.

End-to-end security is capped by the weakest dependency in the execution path (envelope/attestation/entropy).

### Standardization direction

With a canonical dataset schema + runners + composition model, the community can converge on:
- shared benchmark surfaces,
- shared denominators / threat models,
- and eventually shared ABI interfaces (e.g., ERC-7913-style adapters) for real "apples-to-apples".

---

## Next Steps (A / B / C)

### A) Make protocol readiness fully generated (no manual steps)

Add `scripts/report_protocol_readiness.py` that:
- reads `data/results.jsonl`,
- groups by `surface_class`,
- emits a short readiness table:
  - "what limits effective security today"
  - "which assumptions must change for PQ end-to-end"

Wire it into `scripts/make_reports.sh`.

### B) Add at least one Dilithium / ML-DSA alternative surface

Either:
- ZKNoxHQ ETHDILITHIUM benches, or
- another independent implementation with clean verify microbench.

Goal: broaden dataset beyond Falcon + ML-DSA and reduce "single-vendor bias".

### C) Start VRF/randomness track (schema already ready)

Add first "entropy/VRF" benchmark rows under:
- `security_metric_type = H_min`
- explicit threat model field in notes

Even if early rows are partial (microbenches), this establishes the denominator discipline for randomness.

---

## Where to Look (files)

- **Dataset:** `data/results.jsonl`, `data/results.csv`
- **Schema:** `spec/pqsig_userop_schema_v0.1.md`
- **Methodology:** `spec/gas_per_secure_bit_for_grants.md` (methodology hardening doc; despite filename, content is engineering-methodology)
- **Weakest-link report:** `reports/weakest_link_report.md`
- **Entropy/attestation notes:** `reports/entropy_surface_notes.md`
- **Protocol readiness summary:** `reports/protocol_readiness.md`

---

## Contribution Requests (practical)

- Add new scheme benches with:
  - explicit `bench_name`,
  - `repo`, `commit`,
  - and a clear `surface_class`.

- Add new `depends_on` edges for real AA pipelines so weakest-link is computed from actual dependency graphs, not just baseline examples.

- Propose improved normalization conventions for `security_equiv_bits` (keep explicit; avoid implicit claims).
