# PQ Signature Aggregation Context (BLS → PQ) and Why Surface-Aware Benchmarks Matter

## Why BLS “aggregation” is not free
Ethereum consensus uses BLS because it enables efficient aggregation: the final cryptographic check is constant-size
(two pairings), but *practical verification cost* still includes a linear step: reconstructing the aggregate public key
from participation bitfields (e.g., `aggregation_bits`) by summing the relevant committee public keys.

**Key takeaway:** even when the final check is constant-time, real systems pay additional “surface costs” (bitfields,
pubkey selection/summation, protocol plumbing).

## Why post-quantum breaks the old economics
Post-quantum signature families (e.g., hash-based like XMSS as a motivating example) do not support BLS-style algebraic
aggregation. Individual verification becomes expensive and signatures are larger, making “verify thousands per slot” infeasible.

The practical path is **proof-based aggregation**:
- batch raw signatures → produce a succinct proof (“Aggregate”)
- recursively combine proofs across a P2P network (“Merge”)
- submit a final proof for on-chain / consensus verification.

## Two recursion paradigms (high-level)
1) **Brute-force recursion (SNARK-in-SNARK / zkVM-style)**  
   “Merge” proves verification of inner proofs; simpler developer model, but adds prover overhead (VM / verifier arithmetization).

2) **Specialized recursive primitives (folding / split accumulation)**  
   “Merge” combines underlying statements without full proof verification; often more performant, but can shift complexity to
   witness/DA management and may require a final “succinctness” SNARK step.

## Implication for this repository
As Ethereum moves toward PQ-ready paths (especially under AA / new verification routes), we must benchmark and compare costs
*across verification surfaces*, not only “gas per verify”.

This repo standardizes:
- **verification surfaces** (pure verify vs ERC-1271/7913 vs AA validateUserOp/handleOps, etc.)
- **security normalization** (gas per security-equivalent bit)
- **repeatable measurement pipelines** with explicit provenance.
