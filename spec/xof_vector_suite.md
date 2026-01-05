# XOF / PRNG Vector Suite (EVM PQ wiring)

Goal: prevent “different conventions by accident” when benchmarking PQ verifiers on EVM.

This suite standardizes byte-generation for:
- **FIPS SHAKE**: SHAKE128 / SHAKE256 (reference / precompile-oriented)
- **Keccak-CTR XOF**: keccak256-based counter mode (EVM gas-oriented)

## Domain separation (common)
We hash the following preimage prefix:

u16_be(len(domain)) || domain_bytes || seed_bytes || ...

Where `domain` is UTF-8 text (e.g., "MLDSA65|ExpandA|rho0").

## Profiles

### fips_shake128 / fips_shake256
Byte stream = SHAKE(seed, domain) with the common prefix:
u16_be(len(domain)) || domain || seed

### keccak_ctr_xof128 / keccak_ctr_xof256
Byte stream produced by repeating keccak256 blocks:

block_i = keccak256( u16_be(len(domain)) || domain || seed || u32_be(i) || profile_tag )

Where:
- profile_tag = ASCII bytes: "KCTR128" or "KCTR256"
- output stream = block_0 || block_1 || ... truncated to out_len
