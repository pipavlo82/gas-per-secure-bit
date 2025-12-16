#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDORS_DIR="${ROOT_DIR}/vendors"

REPO_URL="${MLDSA_REPO_URL:-https://github.com/pipavlo82/ml-dsa-65-ethereum-verification.git}"
REPO_DIR="${MLDSA_REPO_DIR:-${VENDORS_DIR}/ml-dsa-65-ethereum-verification}"
REF="${MLDSA_REF:-main}"

if [ "${RESET_DATA:-0}" = "1" ]; then
  : > "${ROOT_DIR}/data/results.jsonl"
  : > "${ROOT_DIR}/data/results.csv"
fi


if [ "${RESET_DATA:-0}" = "1" ]; then
  : > "${ROOT_DIR}/data/results.jsonl"
  : > "${ROOT_DIR}/data/results.csv"
fi


mkdir -p "${VENDORS_DIR}"
mkdir -p "${ROOT_DIR}/data"

if [ ! -d "${REPO_DIR}/.git" ]; then
  git clone "${REPO_URL}" "${REPO_DIR}"
fi

cd "${REPO_DIR}"
git fetch --all --prune
git checkout "${REF}"
git pull --ff-only || true

VENDOR_REPO_NAME="$(basename "$(git rev-parse --show-toplevel)")"
VENDOR_COMMIT="$(git rev-parse HEAD)"

run_one () {
  local label="$1"
  local cmd="$2"
  local needle="$3"
  local scheme="${4:-mldsa65}"
  local chain="${5:-EVM/L1}"
  local lambda="${6:-128}"
  local hashprof="${7:-unknown}"
  local notes="${8:-ml-dsa-65-ethereum-verification}"

  echo "[run] ${label}"
  out="$(eval "${cmd}")"
  gas="$(echo "${out}" | python3 "${ROOT_DIR}/scripts/extract_foundry_gas.py" "${needle}")"

  # пишемо бенч у ROOT data/ але з repo/commit від vendor
  cd "${ROOT_DIR}"
  python3 "${ROOT_DIR}/scripts/parse_bench.py" "{
    \"repo\":\"${VENDOR_REPO_NAME}\",
    \"commit\":\"${VENDOR_COMMIT}\",
    \"scheme\":\"${scheme}\",
    \"bench_name\":\"${label}\",
    \"chain_profile\":\"${chain}\",
    \"gas_verify\":${gas},
    \"security_metric_type\":\"lambda_eff\",
    \"security_metric_value\":${lambda},
    \"hash_profile\":\"${hashprof}\",
    \"notes\":\"${notes} (ref=${REF})\"
  }"
  cd "${REPO_DIR}"
}

run_one \
  "verify_poc_foundry" \
  "forge test --match-test test_verify_gas_poc -vv 2>&1" \
  "test_verify_gas_poc"

# важливо: тут беремо LOG-газ, не "(gas: ...)" з Foundry
run_one \
  "preA_compute_w_fromPackedA_ntt_rho0_log" \
  "forge test --match-test test_compute_w_fromPacked_A_ntt_gas_rho0 -vv 2>&1" \
  "gas_compute_w_fromPacked_A_ntt(rho0)"

run_one \
  "preA_compute_w_fromPackedA_ntt_rho1_log" \
  "forge test --match-test test_compute_w_fromPacked_A_ntt_gas_rho1 -vv 2>&1" \
  "gas_compute_w_fromPacked_A_ntt(rho1)"
