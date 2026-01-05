#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDORS_DIR="${ROOT_DIR}/vendors"

REPO_URL="${ETHDILITHIUM_REPO_URL:-https://github.com/ZKNoxHQ/ETHDILITHIUM.git}"
REPO_DIR="${ETHDILITHIUM_REPO_DIR:-${VENDORS_DIR}/ETHDILITHIUM}"
REF="${ETHDILITHIUM_REF:-df999ed4f8032d26d9d3d22748407afbb7978ae7}"

VENDOR_REPO="ZKNoxHQ/ETHDILITHIUM"

if [ "${RESET_DATA:-0}" = "1" ]; then
  mkdir -p "${ROOT_DIR}/data"
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

VENDOR_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
VENDOR_REPO_NAME="${VENDOR_REPO}"

run_one () {
  local label="$1"; shift
  local scheme="$1"; shift
  local chain="$1"; shift
  local lambda="$1"; shift
  local hashprof="$1"; shift
  local notes="$1"; shift
  local match_path="$1"; shift
  local match_test="$1"; shift
  local no_match_test="${1:-}"; shift || true
  local needle="$1"; shift

  echo "[run] ${label}"
  echo "[info] path='${match_path}' match='${match_test}' nomatch='${no_match_test}' needle='${needle}'"

  local cmd=(forge test --match-path "${match_path}" --match-test "${match_test}" -vv)
  if [ -n "${no_match_test}" ]; then
    cmd+=(--no-match-test "${no_match_test}")
  fi

  local out gas
  out="$("${cmd[@]}" 2>&1)"
  gas="$(echo "${out}" | python3 "${ROOT_DIR}/scripts/extract_foundry_gas.py" "${needle}")"

  cd "${ROOT_DIR}"
  python3 "${ROOT_DIR}/scripts/parse_bench.py" "{
    \"scheme\":\"${scheme}\",
    \"bench_name\":\"${label}\",
    \"chain_profile\":\"${chain}\",
    \"gas_verify\":${gas},
    \"security_metric_type\":\"lambda_eff\",
    \"security_metric_value\":${lambda},
    \"hash_profile\":\"${hashprof}\",
    \"notes\":\"${notes} (ref=${REF}; path=${match_path}; match=${match_test}; needle=${needle})\",
    \"provenance\": {\"repo\":\"${VENDOR_REPO_NAME}\", \"commit\":\"${VENDOR_COMMIT}\", \"path\":\"vendors/ETHDILITHIUM\"}
  }"
  cd "${REPO_DIR}"
}

# ETH mode (KAT in test file; exclude FFI-based testVerifyShorter)
run_one \
  "ethdilithium_eth_verify_log" \
  "dilithium" "EVM/L1" 128 "unknown" "ETHDILITHIUM (ETH mode)" \
  "test/ZKNOX_ethdilithium.t.sol" \
  "testVerify" \
  "testVerifyShorter" \
  "Gas used:"

# NIST mode (KAT in test file; exclude FFI-based testVerifyShorter)
run_one \
  "ethdilithium_nist_verify_log" \
  "dilithium" "EVM/L1" 128 "unknown" "ETHDILITHIUM (NIST mode)" \
  "test/ZKNOX_dilithium.t.sol" \
  "testVerify" \
  "testVerifyShorter" \
  "Gas used:"

# P-256 verify micro (useful baseline; already logs Gas used)
run_one \
  "ethdilithium_p256verify_log" \
  "p256" "EVM/L1" 128 "unknown" "ETHDILITHIUM P-256 verify micro" \
  "test/ZKNOX_p256verify.t.sol" \
  "testVerify" \
  "" \
  "Gas used:"
