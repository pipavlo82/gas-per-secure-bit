#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: > data/results.jsonl
: > data/results.csv

# ML-DSA (3 rows)
RESET_DATA=0 MLDSA_REF="${MLDSA_REF:-feature/mldsa-ntt-opt-phase12-erc7913-packedA}" ./scripts/run_vendor_mldsa.sh

# ECDSA (3 rows)
RESET_DATA=0 ./scripts/run_ecdsa.sh

# QuantumAccount/Falcon (4 rows)
QA_REF="${QA_REF:-main}" RESET_DATA=0 ./scripts/run_vendor_quantumaccount.sh

wc -l data/results.jsonl data/results.csv
