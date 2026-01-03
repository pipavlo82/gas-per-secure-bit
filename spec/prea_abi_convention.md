# PreA ABI Convention (packedA_ntt calldata) — draft

This document standardizes an **ABI shape** for supplying a precomputed, bound matrix representation
(`packedA_ntt`) into verifiers on EVM.

Goal: make the "PreA" optimization portable across schemes and implementations by fixing:
- calldata structure
- binding / domain separation expectations
- minimal metadata for provenance + KAT compatibility

This is a **convention**, not yet an EIP. The intent is to keep it compatible with:
- app-facing verification surfaces (ERC-7913 adapters)
- protocol-facing verification surfaces (future precompile / EIP candidate)

---

## Background: what "PreA" is

In ML-DSA-65 (FIPS-204 shape), the verifier needs `A_ntt` (NTT-domain matrix derived from `rho` via ExpandA).
Computing ExpandA + NTT on-chain is expensive.

**PreA** = provide `A_ntt` (or an equivalent packed form) as calldata, and bind it to the verification context
via a commitment (e.g., CommitA), so the verifier can safely accept it without recomputing ExpandA on-chain.

This creates a reusable "protocol surface" idea:
- off-chain / precompile / privileged builder provides `packedA_ntt`
- on-chain verifier checks a binding (commitment) and uses it in `w = A*z − c*t1` in NTT domain

---

## Surface classification

In this repo's surface taxonomy (`spec/case_catalog.md`), PreA-related benches typically map to:
- `sig::erc7913` (app-facing adapters that accept `packedA_ntt`)
- `sig::protocol` (protocol-facing / precompile-style surface, if/when enshrined)
- `pq::verify` (verification core, when measured without adapter boundary)

---

## ABI: canonical function shape

### Minimal interface (conceptual)

```solidity
/// @notice Verify a PQ signature using caller-supplied packedA_ntt.
/// @dev "packedA_ntt" MUST be bound to the verification context (CommitA).
function verifyWithPackedA(
    bytes calldata publicKey,
    bytes calldata messageHash,
    bytes calldata signature,
    bytes calldata packedA_ntt
) external view returns (bool ok);
```

Notes:

- `publicKey`, `signature` are scheme-specific encodings.
- `messageHash` is the pre-hashed digest input used by the scheme (avoid ambiguous hashing in-verifier).
- `packedA_ntt` is scheme-specific but ABI-stable as `bytes`.

---

## Commit/binding requirement

Implementations MUST bind `packedA_ntt` to context with domain separation, for example:

```
commitA = H(
  "PreA/CommitA/v1" ||
  scheme_id ||
  verifier_id ||
  pk_rho ||
  hash_profile ||
  H(packedA_ntt)
)
```

Where:

- `scheme_id` is an agreed short tag (e.g., `"mldsa65"`)
- `verifier_id` optionally distinguishes verifier variants
- `pk_rho` is the matrix seed (e.g., `rho`) extracted from `publicKey`
- `hash_profile` (e.g., `keccak256`) is explicit

This prevents:
- replaying `packedA_ntt` across schemes/contexts
- substitution attacks with unrelated matrices

---

## packedA_ntt format (ML-DSA-65 baseline)

This repo treats the concrete byte layout as scheme-specific, but recommends a stable "v1" for ML-DSA-65:

- Matrix shape: `k x l = 6 x 5`
- Each polynomial: 256 coefficients in NTT domain
- Coeff representation: `uint32` or `uint24`-in-bytes (implementation-defined)
- Canonical packing order (recommended):
  - row-major: `A_ntt[k][l][256]`
  - little-endian coefficient encoding
  - no padding between polynomials

Because implementations differ, `packedA_ntt` MUST be treated as an opaque blob at the ABI layer.
Only the binding (CommitA) and the scheme's internal unpacking rules matter.

---

## Benchmark naming convention (this repo)

To keep dataset records comparable:

- **microbench for PreA compute-w:**
  - `mldsa65::preA_compute_w_fromPackedA_ntt_rho{0,1}_log`

- **adapter-facing PreA surface:**
  - `mldsa65::erc7913_verifyWithPackedA_*`

- **protocol-facing (precompile candidate) surface (vNext):**
  - `mldsa65::precompile_verifyWithPackedA_*` (surface tag: `sig::protocol`)

---

## KAT / test vector expectations

To enable cross-implementation comparability, a KAT bundle should include:

- `pk` (including `rho`)
- `sig`
- `msg_hash`
- `packedA_ntt` (for the same `rho`)
- `commitA` (expected binding output, if exposed)
- expected `ok` flag

Recommended file naming:
```
test_vectors/prea_v1_mldsa65_kat.json
```

---

## Security notes

- Accepting `packedA_ntt` without a binding check is **NOT SAFE**.
- Binding must include explicit domain separation and must incorporate `rho` (or equivalent seed) from the public key.
- If a protocol-facing surface (precompile) emerges, the same ABI shape should be preserved:
  app-facing adapters (ERC-7913) remain compatible, and test vectors remain reusable.
