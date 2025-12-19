# Entropy / attestation surfaces (vNext)

This repo extends beyond signature verification by modeling **entropy and attestation surfaces** as first-class benchmark nodes.

## Why
Even with PQ signatures at the wallet layer, end-to-end security can remain bounded by:
- protocol envelope signatures, and
- classical entropy / ordering / attestation dependencies.

## Dataset approach
- Represent entropy sources as records with `security_metric_type = H_min`.
- Compose pipelines with `depends_on` and compute weakest-link effective security.

## Next benchmarks
- on-chain verify costs for PQ VRF / PQ commitments,
- L2 attestation proof verification (aggregated),
- sequencing / ordering surfaces for AA and rollups.
