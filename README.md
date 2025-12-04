# ML-DSA-65 Ethereum Verification

Minimal, auditable verifier for the NIST FIPS-204 post-quantum signature scheme (ML-DSA-65), designed for Ethereum L2 sequencers, AA wallets, validator recovery, and verifiable-control flows.

This repository provides:

- Standardized raw signature layout for ML-DSA-65  
- Unified domain-separation model  
- Gas-profiling harness comparable to Falcon/Dilithium  
- Reproducible test-vector suite  
- Minimal Solidity verifier stub

## Repository Structure

ml-dsa-65-ethereum-verification/
│
├── solidity/
│   └── MLDSA65Verifier.sol
├── test_vectors/
│   ├── README.md
│   └── vector_001.json
├── scripts/
│   └── mldsa65_sign.py
└── docs/
    └── spec.md

## Goals

1. Define a raw ML-DSA-65 signature format suitable for EVM  
2. Provide equivalent test vectors to Falcon-1024  
3. Benchmark gas performance  
4. Propose a PQ verification standard

## License

MIT License.


