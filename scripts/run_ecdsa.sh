#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="${ROOT_DIR}/bench/ecdsa"

mkdir -p "${ROOT_DIR}/data"

if [ "${RESET_DATA:-0}" = "1" ]; then
  : > "${ROOT_DIR}/data/results.jsonl"
  : > "${ROOT_DIR}/data/results.csv"
fi

cd "${BENCH_DIR}"
out="$(forge test --match-contract ECDSA_Gas_Test -vv 2>&1)"

gas_ecrecover="$(echo "${out}" | python3 "${ROOT_DIR}/scripts/extract_foundry_gas.py" "test_ecdsa_verify_ecrecover_gas")"
gas_bytes65="$(echo "${out}" | python3 "${ROOT_DIR}/scripts/extract_foundry_gas.py" "test_ecdsa_verify_bytes65_gas")"
gas_erc1271="$(echo "${out}" | python3 "${ROOT_DIR}/scripts/extract_foundry_gas.py" "test_ecdsa_erc1271_isValidSignature_gas")"

cd "${ROOT_DIR}"

python3 "${ROOT_DIR}/scripts/parse_bench.py" "{
  \"scheme\":\"ecdsa\",
  \"bench_name\":\"ecdsa_verify_ecrecover_foundry\",
  \"chain_profile\":\"EVM/L1\",
  \"gas_verify\":${gas_ecrecover},
  \"security_metric_type\":\"lambda_eff\",
  \"security_metric_value\":128,
  \"hash_profile\":\"keccak256\",
  \"notes\":\"bench/ecdsa: ecrecover verify (v,r,s)\"
}"

python3 "${ROOT_DIR}/scripts/parse_bench.py" "{
  \"scheme\":\"ecdsa\",
  \"bench_name\":\"ecdsa_verify_bytes65_foundry\",
  \"chain_profile\":\"EVM/L1\",
  \"gas_verify\":${gas_bytes65},
  \"security_metric_type\":\"lambda_eff\",
  \"security_metric_value\":128,
  \"hash_profile\":\"keccak256\",
  \"notes\":\"bench/ecdsa: verifyBytes(sig=65 bytes r||s||v)\"
}"

python3 "${ROOT_DIR}/scripts/parse_bench.py" "{
  \"scheme\":\"ecdsa\",
  \"bench_name\":\"ecdsa_erc1271_isValidSignature_foundry\",
  \"chain_profile\":\"EVM/L1\",
  \"gas_verify\":${gas_erc1271},
  \"security_metric_type\":\"lambda_eff\",
  \"security_metric_value\":128,
  \"hash_profile\":\"keccak256\",
  \"notes\":\"bench/ecdsa: ERC-1271 wallet isValidSignature(bytes32,bytes)\"
}"
