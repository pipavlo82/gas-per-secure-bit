# Case Catalog (AA weakest-link / protocol envelope dominance)

This catalog defines **surface classes** used by the dataset to avoid mixing benchmark scopes.
A **surface class** is a label stored in the JSONL `surface` field (e.g., `sig::erc1271`, `aa::handleOps`).

Important:
- `surface` is a **classification tag**, not a record identifier.
- Multiple benchmarks can share the same `surface`.
- Canonical record IDs remain `scheme::bench_name` (see schema in `spec/gas_per_secure_bit.md`).

---

## Surface Classes (canonical tags)

### env::l1_envelope

Protocol-level transaction envelope assumptions on L1.
Typical example: ECDSA-secp256k1 envelope dominance even when inner wallet auth is PQ.

Use when:
- the record models the *protocol envelope* constraint (not an app contract call).

### aa::validateUserOp

Account Abstraction authentication surface at the `validateUserOp()` boundary.

Use when:
- the measured gas corresponds to validation logic invoked by EntryPoint (or equivalent),
- the surface is not end-to-end `handleOps()`.

### aa::handleOps

Account Abstraction end-to-end execution surface at the `EntryPoint.handleOps()` boundary.

Use when:
- the measurement includes the full AA pipeline overhead (not just signature verification).

### sig::erc1271

EIP-1271 contract-wallet signature interface surface (`isValidSignature`).

Use when:
- the measured gas is for the ERC-1271 boundary or a close harness around it.

### sig::erc7913

ERC-7913-style adapter / signature verifier interface (app-facing surface).

Use when:
- the verification boundary is an adapter intended for applications / wallets / AA integration,
- the interface is not intended as an enshrined precompile.

### sig::protocol

Protocol-facing signature interface / precompile surface.

Intended meaning:
- "enshrined" or protocol-level verification boundary (e.g., a precompile or consensus-level signature interface),
- distinct from app-facing adapters (`sig::erc7913`) and contract-wallet (`sig::erc1271`) surfaces.

Use when:
- the measured gas corresponds to a protocol-facing verifier boundary rather than an application contract boundary.

### pq::verify

Pure on-chain PQ verification primitive surface (verification core), excluding protocol envelope overhead.

Use when:
- the benchmark measures a verification core (e.g., Dilithium/Falcon/ML-DSA verify),
- not an AA envelope, not an ERC-1271 wrapper, not a protocol-facing precompile boundary.

### entropy::randao_mix

Protocol-level randomness read surface: access to `RANDAO mix` (or equivalent) used for sampling / selection.

Use when:
- the benchmark measures gas for reading / mixing the randomness source used by protocol logic.

### attestation::relay

Protocol-level attestation relay surface (a proxy for "attestation gating" logic).

Use when:
- the benchmark measures gas for verifying/relaying an attestation-like object or commitment,
- denominators (`H_min`) may be placeholders until the threat model is finalized.

### hash::commitment

Hash-only commitment / domain separation surface (binding and replay-protection primitives).

Use when:
- the benchmark is fundamentally a hash commitment step (not a signature verify).

---

## S4 (vNext): DAS / "The Verge" evaluation surfaces

These surfaces target L1 upgrade evaluation (DAS & statelessness / history sampling).
Gas is measurable on EVM today via proxy harnesses, while the **security denominator** may remain a placeholder
until the threat model is pinned down.

### das::verify_sample_512b

Proxy surface for verifying one DAS sample of size 512 bytes.

Notes:
- This is a *benchmarking proxy* for comparative evaluation.
- Record the denominator explicitly (e.g., `H_min`) and mark placeholder values clearly in `notes`.

### entropy::randao_mix (used by DAS pipelines)

DAS sampling typically depends on randomness selection, so pipelines may depend on:
- `randao::l1_randao_mix_surface` (bench id), with `surface=entropy::randao_mix`.

---

## Weakest-link composition model

For pipelines with dependencies, define:

- `security_model = weakest_link`
- `depends_on = [ ... ]`

and compute:

```
effective_security_bits = min( security_bits(dep_i) )
```

where `security_bits(dep)` is derived from:
`security_metric_type ∈ {security_equiv_bits, lambda_eff, H_min}`.

---

## Notes / policy

- Keep surface classes **orthogonal** to schemes: surfaces answer "where is this verified?"
- Use surface classes to prevent invalid comparisons (e.g., `pq::verify` vs `aa::handleOps`).
- Placeholder records (e.g., gas=0 or provisional denominators) must state that explicitly in `notes`.
- Canonical dependency graphs live in `spec/case_graph.md`.
- **App-facing vs protocol-facing:** `sig::erc7913` and `sig::erc1271` are app-facing surfaces; `sig::protocol` is the protocol-facing surface (precompile / enshrined interface candidate).
