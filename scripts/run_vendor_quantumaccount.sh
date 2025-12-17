#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR_DIR="${ROOT_DIR}/vendors/quantumaccount"

QA_REF="${QA_REF:-main}"
RESET_DATA="${RESET_DATA:-0}"

DATA_DIR="${ROOT_DIR}/data"
JSONL="${DATA_DIR}/results.jsonl"
CSV="${DATA_DIR}/results.csv"

mkdir -p "${DATA_DIR}"

if [[ "${RESET_DATA}" == "1" ]]; then
  : > "${JSONL}"
  : > "${CSV}"
fi

# Ensure vendor repo exists
if [[ ! -d "${VENDOR_DIR}/.git" ]]; then
  mkdir -p "${ROOT_DIR}/vendors"
  git clone --recursive "https://github.com/Cointrol-Limited/QuantumAccount/" "${VENDOR_DIR}"
fi

pushd "${VENDOR_DIR}" >/dev/null

git fetch --all --tags
git checkout "${QA_REF}"
git pull --ff-only

REPO_NAME="QuantumAccount"
COMMIT_SHA="$(git rev-parse HEAD)"

SCHEME="falcon1024"
CHAIN_PROFILE="EVM/L1"
SEC_TYPE="lambda_eff"
LAMBDA="256.0"
HASH_PROFILE="keccak256"

append_row() {
  local bench="$1"
  local gas="$2"
  local notes="$3"

  local json
  json="$(printf \
    '{"repo":"%s","commit":"%s","scheme":"%s","bench_name":"%s","chain_profile":"%s","gas_verify":%s,"security_metric_type":"%s","security_metric_value":%s,"hash_profile":"%s","notes":"%s (ref=%s)"}' \
    "${REPO_NAME}" "${COMMIT_SHA}" "${SCHEME}" "${bench}" "${CHAIN_PROFILE}" "${gas}" \
    "${SEC_TYPE}" "${LAMBDA}" "${HASH_PROFILE}" "${notes}" "${QA_REF}" \
  )"

  python3 "${ROOT_DIR}/scripts/parse_bench.py" "${json}"
}

run_one_gas_paren() {
  local bench="$1"
  local cmd="$2"
  local notes="$3"

  echo "[run] ${bench}"
  local out
  out="$(bash -lc "${cmd}")" || {
    echo "${out}" >&2
    return 1
  }

  local gas
  gas="$(echo "${out}" | sed -n 's/.*(gas: \([0-9]\+\)).*/\1/p' | head -n1)"
  if [[ -z "${gas}" ]]; then
    echo "Failed to parse (gas: N) for ${bench}" >&2
    echo "${out}" >&2
    return 1
  fi

  append_row "${bench}" "${gas}" "${notes}"
  echo "${out}" | grep -E "\[PASS\]" -n || true
}

run_one_gas_logline() {
  local bench="$1"
  local cmd="$2"
  local logkey="$3"
  local notes="$4"

  echo "[run] ${bench}"
  local out
  out="$(bash -lc "${cmd}")" || {
    echo "${out}" >&2
    return 1
  }

  local gas
  gas="$(echo "${out}" | sed -n "s/.*${logkey}[[:space:]]*:[[:space:]]*\\([0-9]\\+\\).*/\\1/p" | head -n1)"
  if [[ -z "${gas}" ]]; then
    echo "Failed to parse ${logkey}: N for ${bench}" >&2
    echo "${out}" >&2
    return 1
  fi

  append_row "${bench}" "${gas}" "${notes}"
  echo "${out}" | grep -E "${logkey}" -n || true
}

# 1) EntryPoint.getUserOpHash (AA helper)
run_one_gas_paren \
  "qa_getUserOpHash_foundry" \
  "forge test --match-test testQuantumAccountGetUserOpHashViaEntry -vv" \
  "QuantumAccount: EntryPoint.getUserOpHash (AA helper)"

# 2) EntryPoint.handleOps end-to-end
run_one_gas_paren \
  "qa_handleOps_userop_foundry" \
  "forge test --match-test testQuantumAccountViaEntryPoint -vv" \
  "QuantumAccount: EntryPoint.handleOps end-to-end (includes AA pipeline)"

# 3) QuantumAccount.validateUserOp (log-reported internal gas)
run_one_gas_logline \
  "qa_validateUserOp_userop_log" \
  "forge test --match-test test_validateUserOp_gas_log -vv" \
  "gas_validateUserOp" \
  "QuantumAccount: QuantumAccount.validateUserOp (account-level validation, no handleOps)"

# 4) Falcon.verifySignature clean micro (log-reported verify-only gas)
run_one_gas_logline \
  "falcon_verifySignature_log" \
  "forge test --match-contract Falcon_GasMicro_Test --match-test test_falcon_verify_gas_log -vv" \
  "gas_falcon_verify" \
  "QuantumAccount/Falcon: Falcon.verifySignature (clean verifySignature only)"

popd >/dev/null
echo "Wrote ${JSONL} and ${CSV}"
