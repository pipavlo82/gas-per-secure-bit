# Gas per secure bit

**Benchmarking post-quantum signatures and verifiable randomness by gas cost per cryptographically secure bit.**

This repository is an experimental lab spun out of  
[`ml-dsa-65-ethereum-verification`](https://github.com/pipavlo82/ml-dsa-65-ethereum-verification).  
Here we are free to break, refactor and experiment without touching the original verifier repo.

The core idea of this project is a simple, chain-aware metric:

\[
\text{Gas per secure bit} = \frac{\text{gas\_verify}}{H_\text{min}(\text{object})}
\]

where

- `gas_verify` – on-chain gas cost to verify a signature or VRF proof,
- \(H_\text{min}\) – min-entropy / effective security level in bits:
  - for signatures – effective security level λ (e.g. 128-bit),
  - for randomness / VRF – min-entropy of the verified random output.

This lets us compare schemes not just by “gas per verify”, but by **gas per actual cryptographic security / entropy**.

---

## Goals

1. **Define the metric**

   - Formalize “gas per secure bit” for:
     - PQ signatures: **ML-DSA-65**, Falcon, Dilithium, ECDSA, BLS.
     - Verifiable randomness sources: Re4ctoR VRF, Chainlink-style VRF, RANDAO-style beacons, etc.
   - Specify how to estimate \(H_\text{min}\) under clear threat models.

2. **Build an open benchmarking suite**

   - Solidity contracts + Foundry tests that:
     - verify signatures and VRF proofs on-chain,
     - record `gas_used`,
     - export results as CSV/JSON for analysis.
   - Include both:
     - classic metrics (`gas_per_call`, `gas_per_byte`),
     - new metric (`gas_per_secure_bit`).

3. **Publish comparable datasets**

   For each scheme / chain profile (Ethereum L1, typical L2s):

   - `scheme`, `chain`, `gas_verify`, `lambda_eff`, `H_min`,
   - `gas_per_secure_bit`, `gas_per_byte`, `latency_ms`, `trust_model`.

4. **Move toward a standard / draft spec**

   - A Markdown spec (can evolve into an EIP / whitepaper) describing:
     - definitions,
     - assumptions,
     - measurement methodology,
     - reporting format for “gas per secure bit”.

---

## Repository layout (planned)

This repo currently contains the imported ML-DSA-65 verifier layout from the original project.  
We will gradually refactor it into the following structure:

- `spec/`  
  Formal documents and drafts:
  - `gas_per_secure_bit.md` – metric definition, threat models, examples.
  - `mldsa_profile.md` – profile for ML-DSA-65 on Ethereum.

- `contracts/`  
  Solidity benchmarks and helpers:
  - `mldsa/` – ML-DSA-65 verifier components (NTT, Poly, PolyVec, Hint, Verifier).
  - `vrf/` – VRF / randomness adapters (Re4ctoR VRF, RANDAO-style beacons, etc.) [future].

- `scripts/`  
  Tooling to run and collect benchmarks:
  - Foundry test runners,
  - small Python helpers to parse gas reports and compute metrics.

- `data/`  
  Generated datasets:
  - CSV/JSON with `gas_per_secure_bit` and `gas_per_byte` for each experiment.

---

## Current status

- `main` branch is a sandbox clone of `ml-dsa-65-ethereum-verification`.
- ML-DSA-65 NTT / verifier contracts and tests are present and working.
- No public benchmark datasets yet – everything is experimental.

---

## Next steps

Short-term roadmap:

1. **Spec**

   - Add `spec/gas_per_secure_bit.md` with:
     - exact formulae,
     - example calculations for ML-DSA-65 (128-bit security),
     - notes on how we treat min-entropy for randomness sources.

2. **ML-DSA-65 benchmark**

   - Extract the verifier into `contracts/mldsa/`.
   - Add a dedicated Foundry test that:
     - runs one or more verification calls,
     - records `gas_used`,
     - emits it in a machine-readable format.

3. **Metric computation**

   - Small script that reads gas results and outputs a table:

     ```text
     scheme,chain,gas_verify,lambda_eff,gas_per_secure_bit
     MLDSA65,ethereum,2700000,128,21093.75
     ```

4. **VRF / randomness**

   - Add first adapter for a verifiable randomness source (e.g. Re4ctoR VRF).
   - Define and compute `gas per verifiable random bit` using the same framework.

---

## Notes

- This repo is intentionally experimental.  
  Code and structure may change aggressively while we explore the metric.
- Once the methodology stabilizes, the spec and benchmark suite can be split out
  into a more formal “standard” repository and referenced by other projects.
