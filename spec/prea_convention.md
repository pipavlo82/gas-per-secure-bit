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
## Wire format (calldata) for `packedA_ntt`

### Inputs carried on-chain

When using the PreA path, the verifier receives:

- `pk: bytes` — ML-DSA-65 public key (FIPS-204 shape)
- `sig: bytes` — ML-DSA-65 signature (FIPS-204 shape)
- `msgHash: bytes32` — message digest (already domain-separated by the caller)
- `packedA_ntt: bytes` — deterministic encoding of the full `A_ntt` matrix (NTT-domain)
- `commitA: bytes32` — binding commitment to prevent matrix substitution

### Canonical calldata layout (recommended)

`verifyWithPackedA(pk, sig, msgHash, packedA_ntt, commitA)`

- `packedA_ntt` MUST be fixed-length for the selected scheme parameters.
- `packedA_ntt` MUST be deterministic and versioned.

Recommended structure:

- `format_id: bytes4` (e.g. `0x50524541` = "PREA")
- `version: uint8` (e.g. `1`)
- `params_id: uint8` (optional; e.g. identifies ML-DSA-65 / shape)
- `payload: bytes` (the matrix bytes, row-major, deterministic coeff order)

> Note: the exact payload packing is intentionally a *separate spec decision*.
> This document standardizes the *wire contract* (what is passed + how it is bound),
> not the internal compression format.

## CommitA binding (anti-substitution)

### Threat: matrix substitution
An adversary (bundler, relayer, middleware, or L2 operator) may try to replace
`packedA_ntt` with another matrix that changes `w = A*z - c*t1` while keeping other
inputs unchanged.

### Binding rule (normative)

Verifier MUST enforce:

1) `hashA = keccak256(packedA_ntt)`
2) `context = keccak256(abi.encodePacked(chainid, address(this)))` (minimum viable domain separation)
3) `commitA_expected = keccak256(abi.encodePacked(
       "PreA/MLDSA65/v1",
       msgHash,
       hashA,
       context
   ))`
4) `require(commitA == commitA_expected)`

Notes:
- Including `msgHash` binds `packedA_ntt` to a specific message context (prevents reuse across unrelated messages).
- `context` prevents cross-chain / cross-verifier replay.
- If you also want to bind to `rho`, include it *explicitly* (only if `rho` is a caller-visible input):
  `... abi.encodePacked("PreA/MLDSA65/v1", rho, msgHash, hashA, context)`

## ABI reference (quick)

### Solidity interfaces (minimal)

```solidity
interface IPreA_MLDSA65_Verifier {
    function verify(bytes calldata pk, bytes calldata sig, bytes32 msgHash) external view returns (bool);

    function verifyWithPackedA(
        bytes calldata pk,
        bytes calldata sig,
        bytes32 msgHash,
        bytes calldata packedA_ntt,
        bytes32 commitA
    ) external view returns (bool);
}

ERC-7913 style adapter (common in AA / wallets)
interface IERC7913SignatureVerifier {
    function verify(bytes32 hash, bytes calldata signature) external view returns (bytes4);
}


## Notes

PreA is intentionally orthogonal to how `A` is generated (SHAKE/Keccak backend).
It standardizes the *wire format* and *binding* so ecosystems can compare apples-to-apples.
