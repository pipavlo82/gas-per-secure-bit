#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDORS_DIR="${ROOT_DIR}/vendors"

REPO_URL="${MLDSA_REPO_URL:-https://github.com/pipavlo82/ml-dsa-65-ethereum-verification.git}"
REPO_DIR="${MLDSA_REPO_DIR:-${VENDORS_DIR}/ml-dsa-65-ethereum-verification}"
REF="${MLDSA_REF:-main}"

VENDOR_REPO="pipavlo82/ml-dsa-65-ethereum-verification"

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

# Find a test file containing ANY of the needles (first match wins).
find_test_file_any () {
  # usage: find_test_file_any needle1 needle2 ...
  local n
  for n in "$@"; do
    local f=""
    f="$(grep -RIl --exclude-dir=lib --exclude-dir=out --exclude-dir=cache -- "${n}" test 2>/dev/null | head -n 1 || true)"
    if [ -n "${f}" ]; then
      echo "${f}|${n}"
      return 0
    fi
  done
  echo ""
  return 0
}

# Print a quick index of available tests (top lines).
print_test_index () {
  echo "---- vendor test index (top 80 matches) ----" >&2
  # show common patterns: function test_* and match-test hints
  grep -RIn --exclude-dir=lib --exclude-dir=out --exclude-dir=cache \
    -E "function[[:space:]]+test_[A-Za-z0-9_]*|test_[A-Za-z0-9_]*\(" \
    test 2>/dev/null | head -n 80 >&2 || true
}

run_one_auto () {
  local label="$1"
  shift
  local scheme="${1:-mldsa65}"; shift
  local chain="${1:-EVM/L1}"; shift
  local lambda="${1:-128}"; shift
  local hashprof="${1:-unknown}"; shift
  local notes="${1:-ml-dsa-65-ethereum-verification}"; shift
  # remaining args are needles (ordered fallbacks)
  local needles=("$@")

  echo "[run] ${label}"

  local found
  found="$(find_test_file_any "${needles[@]}")"
  if [ -z "${found}" ]; then
    echo "FATAL: could not find any test file containing any of these needles:" >&2
    printf "  - %s\n" "${needles[@]}" >&2
    print_test_index
    exit 3
  fi

  local tf needle
  tf="${found%%|*}"
  needle="${found##*|}"

  echo "[info] matched needle='${needle}' in file='${tf}'"

  # Run only that test file. Extractor will try:
  # - line containing needle + "(gas: N)"
  # - or log-style needle ... gas: N / : N / = N
  local out
  out="$(forge test --match-path "${tf}" -vv 2>&1)"

  local gas
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
    \"notes\":\"${notes} (ref=${REF}; needle=${needle})\",
    \"provenance\": {\"repo\":\"${VENDOR_REPO_NAME}\", \"commit\":\"${VENDOR_COMMIT}\", \"path\":\"vendors/ml-dsa-65-ethereum-verification\"}
  }"
  cd "${REPO_DIR}"
}

# ---- verify POC ----
# Try several historically used names / substrings.
run_one_auto \
  "verify_poc_foundry" \
  "mldsa65" "EVM/L1" 128 "unknown" "ml-dsa-65-ethereum-verification" \
  "test_verify_gas_poc" \
  "MLDSA_VerifyGas" \
  "VerifyGas" \
  "verify() POC" \
  "gas_verify" \
  "test_verify" \
  "verify_poc"

# ---- PreA rho0 log ----
run_one_auto \
  "preA_compute_w_fromPackedA_ntt_rho0_log" \
  "mldsa65" "EVM/L1" 128 "unknown" "ml-dsa-65-ethereum-verification" \
  "gas_compute_w_fromPacked_A_ntt(rho0)" \
  "fromPacked_A_ntt_gas_rho0" \
  "Packed_A_ntt_gas_rho0" \
  "compute_w_fromPacked_A_ntt" \
  "fromPackedA_ntt"

# ---- PreA rho1 log ----
run_one_auto \
  "preA_compute_w_fromPackedA_ntt_rho1_log" \
  "mldsa65" "EVM/L1" 128 "unknown" "ml-dsa-65-ethereum-verification" \
  "gas_compute_w_fromPacked_A_ntt(rho1)" \
  "fromPacked_A_ntt_gas_rho1" \
  "Packed_A_ntt_gas_rho1" \
  "compute_w_fromPacked_A_ntt" \
  "fromPackedA_ntt"
