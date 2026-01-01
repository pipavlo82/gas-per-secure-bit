# PreA convention (packedA_ntt + CommitA binding) for ML-DSA-65 on EVM

## Goal

Reduce on-chain verification gas by moving the expensive `ExpandA(rho) -> A_ntt` work off-chain
and passing a **packed** NTT-domain matrix representation to the verifier, while preserving integrity.

This repo treats "PreA" as a reusable pattern that can be used with ERC-7913-style verifiers.

## Terms

- `rho`: seed for generating matrix `A`
- `A_ntt`: matrix in NTT domain (shape 6x5 polys for ML-DSA-65)
- `packedA_ntt`: canonical packed encoding of `A_ntt` for calldata
- `CommitA`: binding commitment to `packedA_ntt` (prevents matrix substitution)

## Threat model

Adversary may attempt to:
- provide an invalid `packedA_ntt` not derived from `rho`
- swap `packedA_ntt` between signatures / messages
- replay `packedA_ntt` across different contexts

We mitigate by binding `packedA_ntt` via `CommitA` and enforcing domain-separated derivation.

## Canonical calldata

### Recommended function surface

- `verify(bytes pk, bytes sig, bytes32 msgHash) -> bool` (baseline)
- `verifyWithPackedA(bytes pk, bytes sig, bytes32 msgHash, bytes packedA_ntt, bytes32 commitA) -> bool`

Return style can be ERC-1271 / ERC-7913 selectors depending on adapter layer.

### CommitA binding

CommitA MUST be computed as:

CommitA = keccak256(
  "PreA/MLDSA65/v1" || rho || keccak256(packedA_ntt) || context
)

Where `context` is a domain separator that prevents cross-protocol reuse, e.g.:
- chain id
- verifier address
- optional application tag (AA / ERC-4337 / protocol surface)

Minimum viable:
`context = keccak256(chainid || address(this))`

Verifier MUST:
- recompute `keccak256(packedA_ntt)`
- recompute `CommitA` and require equality
- then use `packedA_ntt` in the `compute_w` path

## Encoding: packedA_ntt

`packedA_ntt` is a deterministic byte encoding of the full `A_ntt` matrix.

Requirements:
- fixed length for the chosen scheme parameters
- deterministic coefficient order and endianness
- versioned: include a `format_id` prefix (1 byte or 4 bytes)

Example structure (illustrative):
- 4 bytes: format_id = 0x50415231 ("PAR1")
- then row-major polynomials, each poly is 256 coefficients
- each coefficient encoded as uint32 (or tighter if you have a proven packing)

## Conformance

A PreA implementation is conformant if:
- CommitA binding is enforced
- encoding is deterministic and versioned
- a reference test vector set exists:
  - rho, packedA_ntt, commitA, and a known-good verify() result

## Notes

PreA is intentionally orthogonal to how `A` is generated (SHAKE/Keccak backend).
It standardizes the *wire format* and *binding* so ecosystems can compare apples-to-apples.
