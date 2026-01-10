# Gas per Secure Bit

<div align="center">

**Benchmarking post-quantum signatures and protocol-level randomness surfaces on EVM by gas cost per cryptographically meaningful bit.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built with Foundry](https://img.shields.io/badge/Built%20with-Foundry-FFDB1C.svg)](https://getfoundry.sh/)

</div>

---

## Table of Contents

- [Methodology (surfaces + weakest-link)](#methodology-surfaces--weakest-link)
- [PQ aggregation surfaces (BLS → PQ) — why this matters](#pq-aggregation-surfaces-bls--pq--why-this-matters)
- [Core Metric](#core-metric)
- [Public Review Entry Points](#public-review-entry-points)
- [Why This Exists](#why-this-exists)
- [New: Weakest-link + Protocol Readiness Surfaces](#new-weakest-link--protocol-readiness-surfaces)
- [Reproducible Reports & Data Policy](#reproducible-reports--data-policy)
- [Gas extraction modes (snapshot vs logs)](#gas-extraction-modes-snapshot-vs-logs)
- [XOF Vector Suite (Keccak-CTR vs FIPS SHAKE)](#xof-vector-suite-keccak-ctr-vs-fips-shake)
- [Canonical test vectors + calldata packs](#canonical-test-vectors--calldata-packs)
- [Measured Protocol Surfaces (EVM/L1)](#measured-protocol-surfaces-evml1)
- [Chart](#chart)
- [Current Dataset (EVM/L1) — Gas Snapshots](#current-dataset-evml1--gas-snapshots)
- [What We Built](#what-we-built)
- [Repo Layout](#repo-layout)
- [Dataset Schema (CSV)](#dataset-schema-csv)
- [Security Normalization (Explicit Assumptions)](#security-normalization-explicit-assumptions)
- [Quick Start](#quick-start)
- [PreA Convention (ML-DSA-65)](#prea-convention-ml-dsa-65)
- [Vendor benchmarks (pinned refs)](#vendor-benchmarks-pinned-refs)
- [Benchmarks Included](#benchmarks-included)
- [Related Work / References](#related-work--references)
- [Roadmap](#roadmap)
- [License](#license)
- [Disclaimer](#disclaimer)
- [Maintainer](#maintainer)
- [Citation](#citation)

---

## Methodology (surfaces + weakest-link)

To avoid mixing benchmark scopes, the dataset supports a surface taxonomy and an optional dependency graph:

- **Canonical execution surfaces (S0–S3):** `spec/case_graph.md`
- **Case catalog / baseline nodes:** `spec/case_catalog.md`
- **Weakest-link report (generated):** `reports/weakest_link_report.md`
- **One-page status summary:** `reports/summary.md`

We separate **app-facing** verifier surfaces (ERC-1271 / ERC-7913 / AA) from **protocol-facing** surfaces
(e.g., a precompile-style verifier boundary, tagged as `sig::protocol`) to avoid mixing scopes.

**Surface taxonomy:** ERC-7913 adapters represent the app-facing verification boundary (wallets, dapps, AA integration), while `sig::protocol` (e.g., EIP-7932 candidate) represents a protocol-facing interface (precompile / enshrined verifier boundary).

For any pipeline record with `depends_on[]`:

```
effective_security_bits = min(security_bits(dep_i))
```

Where `security_bits(x)` is derived from records with `security_metric_type ∈ {security_equiv_bits, lambda_eff, H_min}`.

This repo may record multiple denominators for the same bench (e.g., `lambda_eff` for conservative crypto strength and `security_equiv_bits` for declared normalization) as separate records; comparisons must state which denominator is used.

### Gas extraction modes (snapshot vs logs)

Some vendor harnesses expose gas via Foundry snapshot lines `(gas: N)`, while others print it via logs
(e.g., `Gas used: N`). Runners support both via `scripts/extract_foundry_gas.py` using a per-run `needle`
(e.g., `Gas used:`) so vendor repos do not need to be modified.

---

This repository is an experimental benchmarking lab spun out of  
[`ml-dsa-65-ethereum-verification`](https://github.com/pipavlo82/ml-dsa-65-ethereum-verification),
which provides the **on-chain verification artifacts** (Solidity implementation + gas harnesses) used as a primary vendor source.

It exists to answer one practical question for Ethereum engineers:

> **How expensive is "real security" on EVM — once you normalize gas by a declared security target and by protocol constraints?**

In other words: **"gas/verify" is not enough** if the protocol envelope bounds end-to-end security even when the wallet uses PQ signatures.

---

## Core Metric

GitHub does **not** render LaTeX by default, so the canonical formula is written in plain form:

> **gas_per_bit = gas_verify / security_metric_value**

Where:
- **gas_verify** — on-chain gas used to verify a signature / proof (or a verifiable computation step).
- **security_metric_type** — what the denominator represents:
  - for **signatures / proofs (today)**: `security_equiv_bits` (a declared *classical-equivalent bits* normalization convention)
  - for **randomness / VRF / protocol surfaces**: `H_min` (min-entropy of the verified output under an explicit threat model)
- **security_metric_value** — the denominator value in bits.

For the current signature-only dataset, we typically report:

> **gas_per_secure_bit = gas_verify / security_equiv_bits**

This allows apples-to-apples comparisons across schemes at different security targets, **under explicit assumptions**.

---

## Public Review Entry Points

If you have 10 minutes:

1. [reports/protocol_readiness.md](reports/protocol_readiness.md) — protocol constraints and why "gas/verify" can be misleading.
2. [spec/case_catalog.md](spec/case_catalog.md) + [spec/case_graph.md](spec/case_graph.md) — AA weakest-link (envelope dominance) cases + canonical graphs.
3. [spec/gas_per_secure_bit.md](spec/gas_per_secure_bit.md) — definitions, normalization rules, reporting conventions.
4. [spec/xof_vector_suite.md](spec/xof_vector_suite.md) + [data/vectors/xof_vectors.json](data/vectors/xof_vectors.json) — canonical XOF wiring vectors (FIPS SHAKE + Keccak-CTR).
5. [data/results.jsonl](data/results.jsonl) — canonical dataset (CSV + reports are deterministically rebuilt from it).

---

## Why This Exists

Most public comparisons stop at "gas per verify". That hides critical differences:

- Different security levels (e.g., ECDSA ~128-bit convention vs ML-DSA-65 ~192 vs Falcon-1024 ~256)
- Different verification surfaces (EOA vs ERC-1271 vs EIP-4337 pipeline)
- Different protocol envelopes (e.g., L1 constraints can bound end-to-end security regardless of wallet scheme)

This repo focuses on:
- **normalized units** (gas per declared security-equivalent bit), and
- **protocol-aware interpretation** (weakest-link / envelope dominance).

This is designed to compare not only **gas**, but also **what actually bounds security in protocol-aligned paths** (envelopes, attestations, entropy dependencies).

---

## New: Weakest-link + Protocol Readiness Surfaces

Besides single-bench gas numbers, this repo also models **end-to-end PQ readiness** of real execution paths.

- **Weakest-link security:** for a pipeline record with `depends_on`, the effective security is the minimum across dependencies.
  - Example: AA/UserOp paths can be PQ at the wallet layer but still be bounded by the **L1 envelope** assumption.
- **Entropy / attestation surfaces:** measured protocol surfaces (RANDAO, relay attestation) with `H_min` denominators.

Reports:
- [`reports/weakest_link_report.md`](reports/weakest_link_report.md)
- [`reports/protocol_readiness.md`](reports/protocol_readiness.md)
- [`reports/entropy_surface_notes.md`](reports/entropy_surface_notes.md)

### Weakest-link composition (why normalization matters)

- Mermaid diagram: [`spec/weakest_link.mmd`](spec/weakest_link.mmd)
- Example (Falcon Cat5 bounded by ECDSA envelope): [`spec/weakest_link_falcon_ecdsa.mmd`](spec/weakest_link_falcon_ecdsa.mmd)

---

## Reproducible Reports & Data Policy

This repository follows a **single canonical source of truth** model for benchmark data and reports.

## Canonical test vectors + calldata packs

To keep benchmarks comparable across implementations, this repo treats test vectors and calldata conventions as **external, pinned artifacts**.

Canonical packs live in **pqevm-vector-packs** (vectors + calldata shapes):
- repo: https://github.com/pipavlo82/pqevm-vector-packs
- purpose: single source of truth for (scheme, variant, packing, calldata) so different projects do not benchmark different conventions

This repo may reference packs via dataset metadata fields (e.g. `vector_pack_ref`, `vector_pack_id`, `vector_id`) when available.


### Canonical Data

- **`data/results.jsonl`** is the **only canonical input**.
- Each line is exactly one JSON object (JSONL).
- All edits, additions, and corrections must be done in `data/results.jsonl` only.

### Derived Artifacts

The following files are **derived deterministically** and **must not be edited by hand**:

- `data/results.csv`
- `reports/summary.md`
- `reports/weakest_link_report.md`
- `reports/protocol_readiness.md`
- `docs/gas_per_secure_bit.svg`
- `docs/gas_per_secure_bit_big.svg`

Charts are derived from `data/results.csv` and must not be edited by hand. They are rebuilt from `data/results.jsonl`.

### Canonical Pipeline

To regenerate all derived files locally:

```bash
bash scripts/make_reports.sh
```

This script will:
1. Rebuild `data/results.csv` from `data/results.jsonl`
2. Validate JSONL integrity
3. Enforce uniqueness of `(scheme, bench_name, repo, commit, chain_profile)`
4. Generate all reports (including protocol readiness)

**Pipeline roles:**
- `scripts/parse_bench.py` — ingestion + `--regen` rebuilds `data/results.csv` from `data/results.jsonl`
- `scripts/make_reports.sh` — runs sanity checks + regenerates all reports
- `scripts/make_protocol_readiness.py` — generates `reports/protocol_readiness.md`
- `scripts/patch_protocol_readiness_*.py` — inject pinned vendor snapshots into `reports/protocol_readiness.md`
  (markers: `MLDSA65_VENDOR_*`, `FALCON_VENDOR_*`, `ETHDILITHIUM_VENDOR_*`; invoked from `scripts/make_reports.sh`)

### CI Enforcement

CI runs the same pipeline and fails if any generated file is not committed.

**CI workflow:** `.github/workflows/reports.yml`  
It runs `./scripts/make_reports.sh` and fails if `git diff` is non-empty.

```bash
git diff --stat
```

If the working tree is not clean after running `make_reports.sh`, the pull request will fail.

### Chain Profiles / L2 Aliases

Multiple records may exist for the same benchmark under different `chain_profile` values (e.g. `EVM/L1`, `EVM/L2:arbitrum_one`). 

These represent execution-equivalent measurements with different fee or threat-model contexts:
- **EVM execution gas is assumed equal** across profiles
- **Data availability / calldata pricing differs** by chain

---

## XOF Vector Suite (Keccak-CTR vs FIPS SHAKE)

To prevent "silent convention drift" across PQ verifier implementations, this repo includes a small **XOF wiring
vector suite** that covers both common EVM-relevant approaches:

- **FIPS SHAKE128/SHAKE256** (standard / precompile-friendly)
- **Keccak-CTR-style XOF** (EVM-constrained / gas-oriented)

### Files
- Spec: `spec/xof_vector_suite.md`
- Vectors: `data/vectors/xof_vectors.json`
- Verifier: `scripts/verify_vectors.py`

### Run locally
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_vectors.py data/vectors/xof_vectors.json
```

### CI
A dedicated workflow validates vectors on every PR:
- `.github/workflows/vectors.yml`

---

## Measured Protocol Surfaces (EVM/L1)

Some protocol-level "surfaces" are now measured for gas on EVM/L1.  
For these entries, **gas is measured**, while the **security denominator** (e.g., `H_min`) may still be a **placeholder** until the threat model is finalized.

Current measured surfaces:

- `randao::l1_randao_mix_surface` — gas = **5,820**, `H_min` = **32** (placeholder)
- `randao::mix_for_sample_selection_surface` — gas = **13,081**, `H_min` = **32** (placeholder)  *(randomness access for DAS sample selection)*
- `attestation::relay_attestation_surface` — gas = **43,876**, `H_min` = **128** (placeholder)
- `das::verify_sample_512b_surface` — gas = **2,464**, `das_sample_bits` = **4096**  *(512B sample verification surface)*

Reproduce measurements and refresh dataset + reports:

```bash
./scripts/run_protocol_surfaces.sh
./scripts/make_reports.sh
```

See also:
- `reports/protocol_readiness.md` (weakest-link readiness table)
- `reports/weakest_link_report.md`
- `reports/summary.md`

---

## Chart

![Gas per secure bit (lower is better)](docs/gas_per_secure_bit_big.svg)

(Full-detail chart: [docs/gas_per_secure_bit.svg](docs/gas_per_secure_bit.svg))

> **NOTE:** Charts are derived from `data/results.csv` (rebuilt from `data/results.jsonl` via `./scripts/make_reports.sh`). If you change normalization conventions (e.g., ML-DSA-65 128 → 192), regenerate the dataset and charts.

---

## Current Dataset (EVM/L1) — Gas Snapshots

**Source of truth:** `data/results.jsonl` (CSV is deterministically rebuilt by `scripts/parse_bench.py --regen` via `./scripts/make_reports.sh`).

> **Normalization note:** For ML-DSA-65 we report `security_equiv_bits=192` (FIPS-204 Category 3 convention) in tables.
> Some raw vendor ingests may also record `lambda_eff=128` as a budgeting denominator; those are clearly labeled as baseline and are not used for "secure-bit" comparisons.

### Signature & AA Benchmarks

| Scheme        | Bench name                                | gas_verify  | security_metric_value (bits) | gas / secure-bit |
|---------------|-------------------------------------------|------------:|-----------------------------:|-----------------:|
| **ECDSA**     | ecdsa_verify_ecrecover_foundry            | 21,126      | 128                          | 165.047          |
| **ECDSA**     | ecdsa_erc1271_isValidSignature_foundry    | 21,413      | 128                          | 167.289          |
| **ECDSA**     | ecdsa_verify_bytes65_foundry              | 24,032      | 128                          | 187.750          |
| **Falcon**    | qa_getUserOpHash_foundry                  | 218,333     | 256                          | 852.863          |
| **ML-DSA-65** | preA_compute_w_fromPackedA_ntt_rho0_log   | 1,499,354   | 192                          | 7,809.135        |
| **ML-DSA-65** | preA_compute_w_fromPackedA_ntt_rho1_log   | 1,499,354   | 192                          | 7,809.135        |
| **Falcon**    | falcon_verifySignature_log                | 10,336,055  | 256                          | 40,375.215       |
| **Falcon**    | qa_validateUserOp_userop_log              | 10,589,132  | 256                          | 41,363.797       |
| **Falcon**    | qa_handleOps_userop_foundry               | 10,966,076  | 256                          | 42,836.234       |
| **ML-DSA-65** | verify_poc_foundry                        | 68,901,612  | 192                          | 358,862.563      |

### Protocol Surfaces (measured)

| Scheme          | Bench name                          | gas_verify | security_metric_value (bits) | gas / secure-bit |
|-----------------|-------------------------------------|----------:|-----------------------------:|-----------------:|
| **RANDAO**      | l1_randao_mix_surface               | 5,820     | 32 (H_min)                   | 181.875          |
| **RANDAO**      | mix_for_sample_selection_surface    | 13,081    | 32 (H_min)                   | 408.781          |
| **Attestation** | relay_attestation_surface           | 43,876    | 128 (H_min)                  | 342.781          |
| **DAS**         | verify_sample_512b_surface          | 2,464     | 4096 (das_sample_bits)       | 0.602            |

**Note:** Protocol surfaces use `security_metric_type=H_min`; the current H_min values are declared placeholders until the threat model is pinned down. Gas numbers are measured; denominators are provisional. For surfaces, `gas_verify` denotes the measured gas of the surface operation/harness. For `das_sample_bits`, the denominator is not security bits but data size (512 bytes × 8 = 4096 bits), so this represents "gas per verified data bit" (budgeting), not "gas per secure-bit".

**Dataset currently stores ML-DSA rows as `lambda_eff=128`; the 192-bit normalization is shown in reports vendor block / notes.**

**Notes:**
- `qa_handleOps_userop_foundry` includes the full EIP-4337 pipeline (`EntryPoint.handleOps`), so it is **not** a "pure signature verify" cost.
- `falcon_verifySignature_log` is a **clean verifySignature-only** microbench extracted from QuantumAccount logs.
- `verify_poc_foundry` for ML-DSA-65 is a full decode + checks + `w = A*z − c*t1` POC (FIPS-204 shape), built for correctness + reproducibility.

---

## What We Built

A reproducible benchmark lab with:

### Dataset + Schema
- Canonical dataset: `data/results.jsonl` (source of truth)
- Derived table: `data/results.csv`
- Schema/spec documents under `spec/`
- `scripts/parse_bench.py --regen` deterministically rebuilds `data/results.csv` from `data/results.jsonl`

### Runners (Reproducible Ingestion)
- `scripts/run_vendor_mldsa.sh` — ML-DSA-65 (Foundry gas + log extraction for PreA)
- `scripts/run_vendor_ethdilithium.sh` — Dilithium (ZKNoxHQ/ETHDILITHIUM) benches
- `scripts/run_vendor_quantumaccount.sh` — QuantumAccount (Falcon) benches + log-based gas extraction
- `scripts/run_ecdsa.sh` — ECDSA baselines (ecrecover, bytes65 wrapper, ERC-1271)
- `scripts/run_protocol_surfaces.sh` — measures protocol surfaces gas (RANDAO mix + relay attestation), replaces old records, regenerates reports

### Protocol Interpretation Layer
- **Weakest-link / envelope dominance** case catalog and canonical graphs:
  - `spec/case_catalog.md`
  - `spec/case_graph.md`
- **Protocol readiness narrative:**
  - `reports/protocol_readiness.md`

---

## Repo Layout

- `bench/` — microbench contracts/tests for local measurement
- `scripts/` — runners + parsers
- `data/` — dataset outputs (CSV/JSONL)
- `docs/` — charts (SVG) derived from dataset
- `spec/` — definitions, methodology, case catalog, schema notes
- `reports/` — narrative reports connecting results to protocol constraints

Vendored repos may be stored under `vendors/`; provenance is always recorded per row. Vendor licensing remains upstream.

---

## Dataset Schema (CSV)

**Tabular format:** `data/results.csv` (derived from canonical `data/results.jsonl`)

Columns:
- `ts_utc` — timestamp UTC
- `repo`, `commit` — provenance of the implementation
- `scheme` — e.g., `mldsa65`, `ecdsa`, `falcon1024`, `randao`, `attestation`
- `bench_name` — benchmark identifier
- `chain_profile` — e.g., `EVM/L1` (extendable to L2 profiles)
- `gas_verify` — gas used for the bench
- `security_metric_type` — e.g., `security_equiv_bits` (signatures) or `H_min` (randomness/VRF/protocol)
- `security_metric_value` — metric value in bits (e.g., 128 / 192 / 256)
- `gas_per_secure_bit` — computed as `gas_verify / security_metric_value`
- `hash_profile` — e.g., `keccak256` or `unknown`
- `notes` — context + refs (runner, branch, extraction method)

Additional (optional) fields used for composed pipelines:
- `security_model` — e.g. `raw` or `weakest_link`
- `depends_on` — list of dependency record keys (`scheme::bench_name`) used to compute effective security

Right now (signature dataset) we primarily use:
- `security_metric_type = security_equiv_bits`
- `security_metric_value ∈ {128.0, 192.0, 256.0}`

For protocol surfaces:
- `security_metric_type = H_min`
- `security_metric_value` = declared min-entropy placeholder

### Provenance (important)

- In `data/results.jsonl`, `provenance` is a nested JSON object, e.g.:
  `{"repo":"ZKNoxHQ/ETHDILITHIUM","commit":"...","path":"vendor/ETHDILITHIUM"}`.
- In `data/results.csv`, `provenance` is stored as a **JSON string** (CSV-escaped quotes).
  This is intentional: it stays parseable by standard CSV tooling + `json.loads()`.

---

## Security Normalization (Explicit Assumptions)

This repo separates:
1. A scheme's **security category** (when applicable), and
2. A declared **security-equivalent bits** normalization value used for comparisons: `security_equiv_bits`.

### Current Working Convention (Signatures; Normalization Only)

| Scheme | Security Category | `security_equiv_bits` | Notes |
|--------|-------------------|----------------------|-------|
| **ECDSA (secp256k1)** | - | 128 | classical security convention |
| **ML-DSA-65 (FIPS-204)** | Category 3 | 192 | classical-equivalent convention |
| **Falcon-1024** | Category 5 | 256 | classical-equivalent convention |

**Important:** These are normalization conventions, not security proofs. The rule is that they are explicit and applied consistently.

**Dilithium normalization** is parameter-set dependent (e.g., Dilithium2/3/5). Until the vendor variant is pinned to a
declared set, ETHDILITHIUM rows are recorded with `lambda_eff=128` for budgeting comparability.

When `security_metric_type=lambda_eff`, the resulting `gas_per_secure_bit` column should be interpreted as a budgeting
ratio (gas per assumed baseline), not a claim of equivalent classical security.

### Optional Baseline Normalization (Separate Metric)

If you want "per 128-bit baseline" as a convenience view:

```
gas_per_128b = gas_verify / 128
```

Label it explicitly as baseline (not "secure-bit").

---

## Quick Start

### Prerequisites
- Linux/WSL recommended
- `git`
- **Foundry** (`forge`)
- Python 3

### Build a Fresh Dataset (ML-DSA + ECDSA + Falcon + Protocol Surfaces)

From repo root:

```bash
cd /path/to/gas-per-secure-bit

# ECDSA (rows)
RESET_DATA=0 ./scripts/run_ecdsa.sh

# Protocol surfaces (RANDAO + relay) — measured + replace semantics
./scripts/run_protocol_surfaces.sh

# ML-DSA (rows)
RESET_DATA=0 MLDSA_REF="feature/mldsa-ntt-opt-phase12-erc7913-packedA" ./scripts/run_vendor_mldsa.sh

# QuantumAccount/Falcon (rows)
QA_REF=main RESET_DATA=0 ./scripts/run_vendor_quantumaccount.sh

# Regenerate derived artifacts (CSV + reports)
bash scripts/make_reports.sh

wc -l data/results.jsonl data/results.csv
tail -n 20 data/results.csv
```

**Note:** If you want to rebuild from scratch, delete `data/results.jsonl` and rerun the runners. Derived files (CSV + reports) will be regenerated automatically.

### Sanity Check: Ensure Benches Are Unique

```bash
cut -d, -f4,5 data/results.csv | tail -n +2 | sort | uniq -c
```

### Summary View (Sorted by gas/bit)

```bash
python3 - <<'PY'
import csv
rows=list(csv.DictReader(open("data/results.csv")))
rows.sort(key=lambda r: float(r["gas_per_secure_bit"]))
for r in rows:
    print(f'{r["scheme"]:10s} {r["bench_name"]:38s} gas={int(r["gas_verify"]):>9,d}  gas/bit={float(r["gas_per_secure_bit"]):>12,.3f}')
PY
```

### Generate Reports

```bash
bash scripts/make_reports.sh
ls -la reports/
```

---

## PreA Convention (ML-DSA-65)

For benchmarks using precomputed `A_ntt` matrices, this repo follows a canonical calldata layout and provides
on-chain execution proofs for reproducibility.

### Documentation
- **PreA (packedA_ntt) convention:** [vendors/ml-dsa-65-ethereum-verification/docs/preA_packedA_ntt.md](vendors/ml-dsa-65-ethereum-verification/docs/preA_packedA_ntt.md)
- **On-chain proof runner:** `vendors/ml-dsa-65-ethereum-verification/script/RunPreAOnChain.s.sol`

### How to reproduce (local anvil)

```bash
# Terminal 1: Start local chain
anvil

# Terminal 2: Run on-chain proof script
forge script vendors/ml-dsa-65-ethereum-verification/script/RunPreAOnChain.s.sol:RunPreAOnChain \
  --rpc-url http://127.0.0.1:8545 \
  --private-key $PK \
  --broadcast -vv
```

### Expected logs
```
gas_compute_w_fromPacked_A_ntt(rho0) 1499354
gas_compute_w_fromPacked_A_ntt(rho1) 1499354
```

This provides a **wiring-consistency proof**: the same `packedA_ntt` construction used in the microbench
is executed on-chain and produces identical rho0/rho1 measurements, with broadcast artifacts saved for audit.

**Note:** the on-chain runner script lives in the ML-DSA vendor repo and is executed via the pinned vendor runner; this repo records the resulting broadcast artifact for reproducibility.

See also:
- Broadcast artifact: `vendors/ml-dsa-65-ethereum-verification/broadcast/RunPreAOnChain.s.sol/31337/run-latest.json`
- Deployed runner contract: `0xe7f1725e7734ce288f8367e1bb143e90bb3f0512` (anvil, chainId=31337)

---

## Vendor benchmarks (pinned refs)

Vendor runners append measurements into `data/results.jsonl` with explicit provenance, then regenerate reports.

```bash
# ML-DSA-65 (pinned ref)
export MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA
bash scripts/run_vendor_mldsa.sh

# Dilithium (ZKNoxHQ/ETHDILITHIUM, pinned commit by default in the runner)
bash scripts/run_vendor_ethdilithium.sh

# Falcon / QuantumAccount (if present)
bash scripts/run_vendor_quantumaccount.sh

# Rebuild CSV + reports (and inject vendor blocks)
bash scripts/make_reports.sh
```

---

## Benchmarks Included

### ML-DSA-65 (FIPS-204 shape)
- `verify_poc_foundry` — full decode + checks + w = A*z − c*t1 verify POC
- `preA_compute_w_fromPackedA_ntt_rho{0,1}_log` — compute_w microbench from packed A_ntt (PreA path)

### ECDSA (bench/ecdsa)
- `ecdsa_verify_ecrecover_foundry`
- `ecdsa_verify_bytes65_foundry`
- `ecdsa_erc1271_isValidSignature_foundry`

### Dilithium (vendor: ZKNoxHQ/ETHDILITHIUM)
Ingested benches (EVM/L1 gas snapshots from the vendor repo):

- `ethdilithium_eth_verify_log` — Dilithium verify (ETH mode), gas extracted from logs
- `ethdilithium_nist_verify_log` — Dilithium verify (NIST mode), gas extracted from logs
- `ethdilithium_p256verify_log` — P-256 verify microbench (log-based) included by the vendor repo

Runner:
- `scripts/run_vendor_ethdilithium.sh`

### Falcon / QuantumAccount (vendor + local copy)
Ingested benches:
- `qa_getUserOpHash_foundry` — EntryPoint helper
- `qa_handleOps_userop_foundry` — end-to-end AA pipeline
- `qa_validateUserOp_userop_log` — account validation path (log-based gas)
- `falcon_verifySignature_log` — clean verifySignature-only microbench (log-based gas)

Local microbench copy:
- `bench/falcon/Falcon_GasMicro.t.sol`

### Protocol Surfaces (measured)
- `randao::l1_randao_mix_surface` — Foundry gas harness (measured)
- `randao::mix_for_sample_selection_surface` — Foundry gas harness (measured)
- `attestation::relay_attestation_surface` — Foundry gas harness (measured)
- `das::verify_sample_512b_surface` — Foundry gas harness (measured)

---

## Related Work / References

### PQ Signatures on EVM
- **NIST FIPS-204 (ML-DSA):** https://csrc.nist.gov/pubs/fips/204/final
- **ZKNoxHQ:**
  - **ETHFALCON:** https://github.com/ZKNoxHQ/ETHFALCON
  - **ETHDILITHIUM:** https://github.com/ZKNoxHQ/ETHDILITHIUM
- **Paul Angus** (Falcon discussions):
  - EthResearch profile: https://ethresear.ch/u/paulangusbark
  - Falcon reference site: https://falcon-sign.info

### Account Abstraction / Wallet Interfaces Used in Benches
- **EIP-4337** (EntryPoint / AA): https://eips.ethereum.org/EIPS/eip-4337
- **EIP-1271** (contract wallet signatures): https://eips.ethereum.org/EIPS/eip-1271

### Vendor Benchmark Sources
- **QuantumAccount** (Falcon1024 AA stack): https://github.com/Cointrol-Limited/QuantumAccount

### Tooling
- **Foundry:** https://getfoundry.sh/

---

## Roadmap

### Near-term
- Harden spec text in `spec/gas_per_secure_bit.md` (definitions, assumptions, reporting rules).
- Add more schemes: Dilithium, BLS, other PQ candidates relevant to EVM.
- Expand "weakest-link" catalog with more protocol cases and explicit attacker models.

### Medium-term
- Add VRF / randomness objects with explicit `H_min` denominators under stated trust models.
- Add L2 profiles (`chain_profile`) and standardize reporting across L1/L2.

### Standardization Track
Converge dataset schema + methodology into a draft spec others can reuse:
- reproducible runners,
- canonical case catalog,
- comparable benchmark definitions,
- explicit security normalization rules.

---

## License

See `LICENSE` (and vendor repo licenses where applicable). This repository records benchmark artifacts and provenance; vendor code remains licensed by upstream.

---

## Disclaimer

This is an experimental benchmarking lab. Results are not a security proof. Use the data as comparative engineering evidence under explicitly stated assumptions.

---

## Maintainer

Maintained by Pavlo Tvardovskyi (GitHub: @pipavlo82)  
Contact: shtomko@gmail.com

---

## Citation

If you use this repository (methodology, dataset schema, runners, or benchmarks) in research or production evaluation, please cite it as:

```
Pavlo Tvardovskyi, gas-per-secure-bit (GitHub repository), 2025.
https://github.com/pipavlo82/gas-per-secure-bit
```

For reproducibility, cite a tag or commit hash.

---

## PQ aggregation surfaces (BLS → PQ) — why this matters

Ethereum's BLS aggregation provides scalability via algebraic structure, but practical verification still includes
linear work to reconstruct aggregate public keys from participation bitfields. Post-quantum signature families lose
this algebraic aggregation property, pushing the system toward **proof-based aggregation** (recursive SNARKs or
folding / accumulation schemes).

As a result, "gas per verify" alone is insufficient: engineering decisions require **surface-aware, security-normalized**
benchmarks across L1/L2/AA verification surfaces and, eventually, PQ aggregation proof verification surfaces.

See: [spec/pq_signature_aggregation_context.md](spec/pq_signature_aggregation_context.md)
