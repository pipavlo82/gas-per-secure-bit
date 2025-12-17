#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR_DIR="${ROOT_DIR}/vendors/quantumaccount"

QA_REF="${QA_REF:-main}"
RESET_DATA="${RESET_DATA:-0}"

if [ "${RESET_DATA}" = "1" ]; then
  mkdir -p "${ROOT_DIR}/data"
  : > "${ROOT_DIR}/data/results.jsonl"
  : > "${ROOT_DIR}/data/results.csv"
fi

# Ensure vendor repo exists
if [ ! -d "${VENDOR_DIR}/.git" ]; then
  mkdir -p "${ROOT_DIR}/vendors"
  git clone --recursive "https://github.com/Cointrol-Limited/QuantumAccount" "${VENDOR_DIR}"
fi

pushd "${VENDOR_DIR}" >/dev/null

git fetch --all --tags
git checkout "${QA_REF}"
git pull --ff-only

REPO_NAME="QuantumAccount"
COMMIT_SHA="$(git rev-parse HEAD)"

# helper: run a command, extract gas from either (a) forge "(gas: N)" or (b) log line prefix
run_one_gas_paren() {
  local bench="$1"
  local cmd="$2"
  local needle="$3"
  local lambda="$4"
  local notes="$5"

  echo "[run] ${bench}"
  local out
  out="$(bash -lc "${cmd}")"

  local gas
  gas="$(echo "${out}" | sed -n 's/.*(gas: \([0-9]\+\)).*/\1/p' | tail -n 1)"
  if [ -z "${gas}" ]; then
    echo "ERROR: could not find '(gas: N)' in forge output" >&2
    echo "${out}" >&2
    exit 1
  fi

  python3 "${ROOT_DIR}/scripts/parse_bench.py" "{
    \"repo\":\"${REPO_NAME}\",
    \"commit\":\"${COMMIT_SHA}\",
    \"scheme\":\"falcon1024\",
    \"bench_name\":\"${bench}\",
    \"chain_profile\":\"EVM/L1\",
    \"gas_verify\":${gas},
    \"security_metric_type\":\"lambda_eff\",
    \"security_metric_value\":${lambda},
    \"hash_profile\":\"keccak256\",
    \"notes\":\"${notes} (ref=${QA_REF})\"
  }"

  echo "${out}" | grep -nE "${needle}|\\(gas:" -n || true
}

run_one_gas_logprefix() {
  local bench="$1"
  local cmd="$2"
  local log_prefix="$3"
  local lambda="$4"
  local notes="$5"

  echo "[run] ${bench}"
  local out
  out="$(bash -lc "${cmd}")"

  local gas
  gas="$(echo "${out}" | sed -n "s/.*${log_prefix}[[:space:]]*\\([0-9]\\+\\).*/\\1/p" | tail -n 1)"
  if [ -z "${gas}" ]; then
    echo "ERROR: could not find log prefix '${log_prefix}' in forge output" >&2
    echo "${out}" >&2
    exit 1
  fi

  python3 "${ROOT_DIR}/scripts/parse_bench.py" "{
    \"repo\":\"${REPO_NAME}\",
    \"commit\":\"${COMMIT_SHA}\",
    \"scheme\":\"falcon1024\",
    \"bench_name\":\"${bench}\",
    \"chain_profile\":\"EVM/L1\",
    \"gas_verify\":${gas},
    \"security_metric_type\":\"lambda_eff\",
    \"security_metric_value\":${lambda},
    \"hash_profile\":\"keccak256\",
    \"notes\":\"${notes} (ref=${QA_REF})\"
  }"

  echo "${out}" | grep -nE "${log_prefix}|\\(gas:" -n || true
}

# 1) AA helper: EntryPoint.getUserOpHash (gas: N)
run_one_gas_paren \
  "qa_getUserOpHash_foundry" \
  "forge test --match-test testQuantumAccountGetUserOpHashViaEntry -vv 2>&1" \
  "getUserOpHash" \
  "256.0" \
  "QuantumAccount: EntryPoint.getUserOpHash (AA helper)"

# 2) end-to-end: EntryPoint.handleOps (gas: N)
run_one_gas_paren \
  "qa_handleOps_userop_foundry" \
  "forge test --match-test testQuantumAccountViaEntryPoint -vv 2>&1" \
  "handleOps" \
  "256.0" \
  "QuantumAccount: EntryPoint.handleOps end-to-end (includes AA pipeline)"

# 3) account-level validation (LOG): gas_validateUserOp: N
run_one_gas_logprefix \
  "qa_validateUserOp_userop_log" \
  "forge test --match-contract QuantumAccount_GasMicro_Test -vv 2>&1" \
  "gas_validateUserOp:" \
  "256.0" \
  "QuantumAccount: QuantumAccount.validateUserOp (account-level validation, no handleOps)"

# 4) clean Falcon verify (LOG): gas_falcon_verify: N
run_one_gas_logprefix \
  "falcon_verifySignature_log" \
  "forge test --match-contract Falcon_GasMicro_Test -vv 2>&1" \
  "gas_falcon_verify:" \
  "256.0" \
  "QuantumAccount/Falcon: Falcon.verifySignature (clean verifySignature only)"

popd >/dev/null

tail -n 15 "${ROOT_DIR}/data/results.csv"
