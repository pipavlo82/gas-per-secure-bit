# Explicit Message Lanes (wormhole prevention)

As Account Abstraction (AA) and post-quantum / hybrid signatures become real deployment targets, we get a combinatorial explosion of verification surfaces (AA validateUserOp, ERC-1271, ERC-7913, protocol-facing precompiles). This creates a quiet but critical class of failures:

**Domain-separation “wormholes”** = replay-by-interpretation across surfaces.
A signature can be cryptographically strong yet become a “strong door in a weak frame” if the signed statement is lane-ambiguous and can be reinterpreted in another context.

This is also a benchmarking problem: without explicit lanes, “gas per verify” can silently compare different semantics.

---

## Minimum bar (v0): versioned lane envelope

All signatures / verifications that are intended to be comparable MUST define a **lane** as a versioned digest envelope that binds:

- `lane_version` (domain tag)
- `chain_id`
- `verifier_binding` (verifying contract address or precompile address/id)
- `surface_id` (which verification surface is in use)
- `algo_id` (including hash/XOF lane and any mode/variant)
- `payload` (surface-defined)

Sketch:

digest = keccak256(abi.encode(
LANE_TAG, // e.g. "EVM_SIG_LANE_V0"
chain_id, // block.chainid
verifier_binding, // contract address or precompile address/id
surface_id, // aa::validateUserOp | sig::erc1271 | sig::erc7913 | sig::protocol | ...
algo_id, // MUST include hash/XOF lane (e.g. *_shake256 vs *_keccakctr)
payload // surface-defined
))

Intent: **no lane ambiguity → no replay-by-interpretation**.

---

## Canonical hybrid ordering (required)

For hybrid signatures, `algo_id` MUST be canonicalized to avoid “same logic, different digest”.

Minimum rule (v0):
- represent hybrids as an ordered set under a fixed canonicalization rule
- e.g. lexicographic order of canonical algorithm identifiers, or registry-defined ordering

Example canonical form:
`hybrid(ecdsa_secp256k1,mldsa65_fips204_shake256_v0)`

---
## Canonical wiring lanes (v0)

These lane IDs are used in `data/results.jsonl` via `wiring_lane` to prevent
scope-mixing (“apples to oranges”) across enforcement paths.

- `EVM_SIG_LANE_V0`
  Native signature verification on EVM (Solidity / contract-level verify surfaces).
  Examples: ERC-7913 verifier ABI, ERC-1271, AA validateUserOp (EntryPoint-bound).

- `EVM_ZK_FROM_PQ_LANE_V0`
  L1 enforcement via ZK proof verification **derived from a PQ signature**.
  This measures “verifier gas + calldata” for a proof system (e.g., Groth16 BN254),
  **not** native PQ signature verification.

## AA-specific guidance

For AA, the **AA-native surface** is `aa::validateUserOp`.

Recommended v0 binding:
- `verifier_binding = EntryPoint address` for the specific UserOp
- `payload = EntryPoint.getUserOpHash(userOp)`

This naturally binds to the EntryPoint version via its address and avoids schema-drift ambiguity.

Wallets MUST NOT “try both” EntryPoints for the same signature, as that reintroduces lane ambiguity.

---

## Protocol/precompile surfaces

For protocol-facing verification, `verifier_binding` can be the **reserved precompile address**.

If a precompile is parameterized (multiple modes/variants), then:
- `algo_id` MUST include the mode/variant so that (`verifier_binding`, `algo_id`) uniquely identifies semantics.

---

## Upgradeability / migration

Lane tags are versioned on purpose:
- Verifiers/wallets MAY accept multiple lane versions (V0 and V1) under an explicit policy (allowlist/timebox).
- New signatures SHOULD target the latest lane.

---

## Benchmark rule (this repo)

Benchmarks intended for cross-project comparison SHOULD declare lane metadata.
If a benchmark does not use explicit lanes, it MUST say so (see dataset fields).

This keeps results reproducible and prevents comparing different semantics as if they were the same.

