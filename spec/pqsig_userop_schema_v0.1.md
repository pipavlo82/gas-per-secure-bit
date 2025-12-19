# PQSig UserOp Schema v0.1 (draft)

Goal: a minimal, cross-implementation JSON payload to enable interoperability and cross-testing
between EVM PQ signature verifiers (ML-DSA/Falcon/Dilithium, etc.) in AA contexts.

## Design principles
- Minimal unit: **userOp + encoded public key** (+ encoded signature), plus explicit hashing/XOF wiring metadata.
- Explicitness: avoid accidental "different hash conventions" comparisons.
- Extensible: allow adding scheme-specific fields without breaking the base shape.

## Canonical object (top-level)
Required fields:
- `version` : string, must be `"pqsig-userop-v0.1"`
- `scheme`  : string (e.g. `"mldsa65"`, `"falcon1024"`, `"dilithium5"`)
- `chain_profile` : string (e.g. `"EVM/L1"`, `"EVM/L2"`)
- `user_op` : object (EIP-4337 UserOperation-like shape or a minimal subset)
- `pubkey`  : object
- `signature` : object
- `hashing` : object (explicit wiring)

Optional:
- `context` : free-form metadata (bench_name, repo, commit, notes, etc.)

## user_op
For v0.1, we keep it simple: include **raw bytes** if you already have a canonical encoding,
otherwise include the structured fields.

Either:
- `user_op.encoded` : 0x-hex bytes (canonical packed encoding used for signing)

Or:
- `user_op.fields` : object with AA fields (sender, nonce, callData, etc.) + an agreed packing rule.
(If using `fields`, you MUST specify `user_op.packing`.)

Recommended for v0.1 interoperability: use `user_op.encoded`.

## pubkey
Required:
- `pubkey.encoded` : 0x-hex bytes (scheme-specific encoded public key)

Optional:
- `pubkey.format` : string (e.g. `"fips204_mldsa65_pk"`, `"falcon_pk"`)
- `pubkey.notes`

## signature
Required:
- `signature.encoded` : 0x-hex bytes (scheme-specific encoded signature)

Optional:
- `signature.format` : string (e.g. `"fips204_mldsa65_sig"`, `"falcon_sig"`)
- `signature.notes`

## hashing (critical for apples-to-apples)
Required:
- `hashing.message` : string, what is hashed/signed
  - `"userOp_encoded"` (recommended)
  - `"userOpHash"` (EIP-4337 hash)
  - `"custom"`
- `hashing.domain` : string, domain separation strategy
  - `"none"`
  - `"eip712"`
  - `"custom"`
- `hashing.hash_fn` : string
  - `"keccak256"`
  - `"sha256"`
  - `"shake128"`
  - `"shake256"`
- `hashing.xof_wiring` : string, if an XOF is involved
  - `"none"`
  - `"keccak_shake_compat"` (placeholder naming; see notes)
  - `"custom"`
- `hashing.digest` : optional 0x-hex bytes (if you want to pin exact digest used)

Notes:
- If `hashing.hash_fn` is an XOF, define how bytes are expanded (length, personalization, counters, etc.)
  via `hashing.xof_wiring` or a future detailed sub-object.

## Intended use
- Store vectors in JSON (one object per vector)
- Allow cross-implementation testing by re-deriving the digest and verifying signature
- Enable benchmark comparisons with explicit wiring assumptions

## Status
Draft v0.1. Expected to evolve once multiple implementations consume it.

## Optional fields (vNext, backward-compatible)

These fields are OPTIONAL. Existing records remain valid without them.

- schema_version: string (e.g. "0.2")
- surface_class: string enum
  - L1_envelope
  - AA_userop_auth
  - ERC1271_contract_verify
  - PQ_verify_onchain
  - Entropy_attestation
  - Hash_commitment
- security_model: string enum
  - raw
  - weakest_link
- depends_on: array[string] (default: [])
- provenance: object (optional)
  - repo: string (upstream repo name)
  - commit: string (upstream git commit hash)
  - path: string (optional)
  - toolchain: string (optional)
