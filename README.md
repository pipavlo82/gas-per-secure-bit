ML-DSA-65 Ethereum Verification

Post-quantum verification for Solidity (FIPS-204, ML-DSA-65).

This repository provides the first minimal, auditable ML-DSA-65 (FIPS-204) verifier prototype for Ethereum.
It is designed for:

• L2 sequencers
• ERC-4337 AA bundlers
• Validator key-recovery flows
• Verifiable randomness consumers
• PQ migration paths for existing ECDSA-based systems

The repo includes Foundry test harnesses, real-world signatures from an R4 entropy node, and a clean Solidity verifier scaffold.

Features
✓ ML-DSA-65 (FIPS-204) raw signature decoding

Base64 → bytes → structured ML-DSA-65 format.
Interoperable with R4 PQ-randomness API and reproducible vectors.

✓ Solidity verification scaffold

solidity/IPQVerifier.sol contains:

• length & scheme validation
• Keccak256 message hashing
• parsing of signature components
• hook for polynomial/NTT verification (to be extended)

Ready to replace Falcon-1024 verification in QuantumAccount.

✓ Reproducible ML-DSA-65 test vectors

Generated via R4 gateway:

curl -H "X-API-Key: demo" http://localhost:8082/random_dual?sig=pq


Stored under test_vectors/.

✓ Foundry tests

Two test suites:

• test/MLDSA_RealVector.t.sol — JSON + Base64 + structure decoding
• test/MLDSA_Verify.t.sol — calls verifier contract

Covers the entire ML-DSA-65 pipeline up to logic stub.

Repository Structure
ml-dsa-65-ethereum-verification/
│
├── solidity/
│   ├── MLDSA65Verifier.sol        # reference verifier
│   └── IPQVerifier.sol            # integration verifier
│
├── test/
│   ├── MLDSA_RealVector.t.sol     # parses real R4 PQ vectors
│   └── MLDSA_Verify.t.sol         # verify() test
│
├── test_vectors/
│   ├── README.md
│   └── vector_001.json
│
├── scripts/
│   ├── decode_vectors.py
│   ├── decode_real_pq.py
│   └── mldsa65_sign.py (optional)
│
├── foundry.toml
└── docs/
    └── spec.md

Generating Real ML-DSA-65 Vectors (R4 Node)

Ensure local R4 gateway is running on localhost:8082.

curl -s "http://localhost:8082/random_dual?sig=pq" \
  -H "X-API-Key: demo" \
  > test_vectors/vector_001.json


Contents include:

• random
• msg_hash
• ECDSA signature
• ML-DSA-65 signature (Base64)
• ML-DSA-65 pubkey (Base64)
• scheme

Running Tests

Install forge-std:

forge install foundry-rs/forge-std --no-commit


Run all tests:

forge test -vvv


Run ML-DSA vector test:

forge test -vvv --match-test test_real_vector


You should see:

[PASS] test_real_vector()
[PASS] test_verify_pq_signature()

Solidity Integration (QuantumAccount)
1. Hashing

ML-DSA-65 challenge is SHAKE256, but Ethereum domain separation uses keccak256.

bytes32 msgHash = keccak256(abi.encodePacked(domain, payload));

2. Signature validation in IPQVerifier
require(sig.length == EXPECTED_SIG_LEN, "invalid signature length");
require(pub.length == EXPECTED_PK_LEN, "invalid public key length");
require(scheme == MLDSA65, "wrong PQ scheme");

3. Use inside ERC-4337 / AA wallet
bool ok = IPQVerifier.verify(pubkey, signature, msgHash);
require(ok, "PQ signature invalid");


Supports hybrid mode:

• ECDSA (current)
• ML-DSA-65 (post-quantum)
• Dual-signature validation for VRF or validator proof-of-control

Roadmap
A) Full Solidity ML-DSA-65 verifier

Polynomial ops
NTT
Hint bits
Challenge building
Norm checks

B) Gas benchmarks

Current expectations:

• Falcon-1024 ≈ 10–12M gas
• ML-DSA-65 ≈ 18–22M gas (before optimization)

C) PQ Verification ABI Standard

Equivalent of OpenZeppelin’s ECDSA.sol but for PQ.

Contributing

PRs welcome for:

• NTT gas optimization
• in-Solidity SHAKE128/256
• polynomial operations
• Falcon vs ML-DSA-65 cross-benchmarks
• AA wallet integration examples

License

MIT License.

