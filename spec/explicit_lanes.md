# Explicit Message Lanes (Domain-Separation “Wormholes”)

## Problem: replay-by-interpretation (“wormholes”)
In PQ / hybrid systems the same bytes can be *validly interpreted* across different verification surfaces
(EOA-style verify, ERC-1271, ERC-7913 adapters, AA validateUserOp, L2/protocol precompile surfaces).
If a signature (or verification transcript) is not bound to the *intended surface + verifier*, an attacker can replay it
by changing the interpretation context.

**Concrete example (classical → AA):**
A signature accepted for an ERC-1271 login or offchain authorization may be replayed as an AA authorization
(if the digest does not bind EntryPoint + surface_id), resulting in unintended onchain effects.

This document defines a minimal “lane envelope” that MUST be bound into the signed/verified digest to prevent such replays.

---

## Definitions
- **Lane**: a domain-separated message channel defined by a canonical envelope.
- **Wormhole**: a cross-surface replay enabled by ambiguous interpretation of the same byte payload.
- **Surface**: the verification context (e.g., `erc1271::isValidSignature`, `aa::validateUserOp`, `erc7913::verify`).
- **Verifier binding**: the concrete verifier address (or protocol binding) that must be included in the digest.

---

## Minimum bar (Lane v0): what MUST be bound
A lane digest MUST commit to:

1. `lane_version` (DOMAIN_TAG)
2. `chainId`
3. `verifierBinding`
4. `surface_id`
5. `algo_id` (including hash/XOF lane identity)
6. `payload` (the message / transcript being authorized)

### Canonical lane envelope (v0)
Use a single canonical encoding rule. Recommended shape:

- `lane_version`: `bytes32` constant tag, e.g. `keccak256("GASPERSECBIT_LANE_V0")`
- `chainId`: `uint256`
- `verifierBinding`: `address` (or `bytes32` for protocol binding, see below)
- `surface_id`: `bytes32` identifier (string-hashed taxonomy key)
- `algo_id`: `bytes32` identifier (MUST include hash/XOF identity)
- `payload`: `bytes`

#### Suggested encoding
- EVM / Solidity: `abi.encode(lane_version, chainId, verifierBinding, surface_id, algo_id, keccak256(payload))`
- Final digest: `keccak256(encoded)` or algorithm-specific prehash (documented under `algo_id`).

**Note:** `algo_id` MUST include the prehash/XOF used inside the signature scheme (e.g., SHAKE256 vs Keccak-based XOF wiring),
so that “same signature, different prehash lane” is impossible.

---

## Canonicalization rules
### Hybrid ordering (multi-sig / hybrid stacks)
When multiple algorithms are present (e.g., ECDSA + ML-DSA-65), ordering MUST be deterministic.

Recommended rule (v0):
1. Sort signers/algorithms by `(algo_registry_id, pubkey_bytes)` where:
   - `algo_registry_id` is a stable registry number (preferred), else
   - lexicographic sort by `algo_id` as a fallback.
2. Concatenate in that order to form the compound verification transcript.

This avoids ambiguity (“swap order” wormholes) across implementations.

---

## Migration policy (V0 → V1)
- Verifiers MAY accept multiple lane versions temporarily via an allowlist/timebox.
- Datasets MUST record which lane version is used.
- A production protocol/app should aim to deprecate older lanes quickly once deployed.

---

## Benchmark rule (dataset requirement)
Every benchmark record MUST declare whether explicit lanes are used.

Minimum dataset annotation:
- `wiring_lane` (string enum):
  - `explicit_v0` — uses the envelope defined in this document
  - `implicit_none` — no explicit lane binding (wormhole risk)
  - `partial` — binds some fields but not the full minimum bar (MUST explain in notes)

If a benchmark is `implicit_none` or `partial`, the record MUST include a short note explaining what is missing
(e.g., “no surface_id binding”, “no verifierBinding/EntryPoint binding”, “algo_id does not include hash/XOF lane”).

---

## Protocol binding notes
If the surface is protocol-facing (e.g., future precompile), `verifierBinding` may be expressed as:
- `address` for deployed contracts/verifiers, or
- `bytes32` domain tag for protocol modules (e.g., `keccak256("EIP-7932:MLDSA65_PRECOMPILE")`).

The critical property is that binding is unambiguous and verifiable in the target execution environment.
