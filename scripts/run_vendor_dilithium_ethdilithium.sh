#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR_DIR="${ROOT}/vendors/ETHDILITHIUM"

: "${DIL_REPO_URL:=https://github.com/ZKNoxHQ/ETHDILITHIUM.git}"
: "${DIL_REF:=df999ed4f8032d26d9d3d22748407afbb7978ae7}"

# Optional knobs
: "${RESET_DATA:=0}"
: "${CHAIN_PROFILE:=evm-l1}"
: "${LAMBDA_EFF:=128}"

# Denominators (set once you confirm the exact Dilithium variant/category)
: "${SEC_BITS_NIST:=128}"
: "${SEC_BITS_EVM:=128}"

# Bench names (stable dataset keys)
: "${DIL_BENCH_NIST:=dilithium_verify_nistkat}"
: "${DIL_BENCH_EVM:=ethdilithium_verify_evmfriendly}"

mkdir -p "${ROOT}/.tmp"
LOG_NIST="${ROOT}/.tmp/ethdil_nist.log"
LOG_EVM="${ROOT}/.tmp/ethdil_evm.log"

MATCH_PATH_NIST="test/ZKNOX_dilithiumKATS.t.sol"
MATCH_PATH_EVM="test/ZKNOX_ethdilithiumKAT.t.sol"
MATCH_TEST="testVerify"

if [[ ! -d "${VENDOR_DIR}/.git" ]]; then
  echo "[dil] cloning ${DIL_REPO_URL} -> ${VENDOR_DIR}"
  git clone "${DIL_REPO_URL}" "${VENDOR_DIR}"
fi

cd "${VENDOR_DIR}"
git fetch --all --tags
git checkout -f "${DIL_REF}"
PINNED_COMMIT="$(git rev-parse HEAD)"

echo "[dil] pinned commit: ${PINNED_COMMIT}"
echo "[dil] repo path: vendors/ETHDILITHIUM"

if [[ -f .gitmodules ]]; then
  echo "[dil] updating submodules"
  git submodule update --init --recursive
fi

echo "[dil] running Foundry gas tests (path-pinned)"
forge test --match-path "${MATCH_PATH_NIST}" --match-test "${MATCH_TEST}" -vv | tee "${LOG_NIST}"
forge test --match-path "${MATCH_PATH_EVM}"  --match-test "${MATCH_TEST}" -vv | tee "${LOG_EVM}"

extract_gas() {
  local logfile="$1"
  local n
  n="$(grep -Eo '\(gas: [0-9]+\)' "${logfile}" | head -n1 | tr -cd '0-9' || true)"
  if [[ -z "${n}" ]]; then
    echo "0"
  else
    echo "${n}"
  fi
}

GAS_NIST="$(extract_gas "${LOG_NIST}")"
GAS_EVM="$(extract_gas "${LOG_EVM}")"

echo "[dil] gas nist: ${GAS_NIST}"
echo "[dil] gas evm : ${GAS_EVM}"

ROW1="${ROOT}/.tmp/ethdil_row_nist.json"
ROW2="${ROOT}/.tmp/ethdil_row_evm.json"

# Write robust JSON via Python to avoid escaping/newline issues.
export GAS_NIST GAS_EVM SEC_BITS_NIST SEC_BITS_EVM LAMBDA_EFF CHAIN_PROFILE PINNED_COMMIT
export DIL_BENCH_NIST DIL_BENCH_EVM

python3 - <<PY
import json
from pathlib import Path
import os

root = Path(os.environ["ROOT"]) if "ROOT" in os.environ else Path(".").resolve()
row1 = Path(os.environ["ROW1"]) if "ROW1" in os.environ else Path("${ROW1}")
row2 = Path(os.environ["ROW2"]) if "ROW2" in os.environ else Path("${ROW2}")

gas_nist = int(os.environ["GAS_NIST"])
gas_evm  = int(os.environ["GAS_EVM"])
sec_nist = int(os.environ["SEC_BITS_NIST"])
sec_evm  = int(os.environ["SEC_BITS_EVM"])
lam      = int(os.environ["LAMBDA_EFF"])
chain    = os.environ["CHAIN_PROFILE"]
commit   = os.environ["PINNED_COMMIT"]

bench_nist = os.environ["DIL_BENCH_NIST"]
bench_evm  = os.environ["DIL_BENCH_EVM"]

def note(gas:int, sec:int) -> str:
    gpb = (gas / sec) if gas and sec else 0
    return f"sec{sec}={sec} gpb{sec}={gpb}"

common = dict(
    scheme="dilithium",
    surface_class="sig::verify",
    chain_profile=chain,
    repo="ZKNoxHQ/ETHDILITHIUM",
    commit=commit,
    provenance={"repo": "ZKNoxHQ/ETHDILITHIUM", "commit": commit, "path": "vendors/ETHDILITHIUM"},
    security_model="standalone",
)

r1 = dict(common)
r1.update(
    bench_name=bench_nist,
    gas_verify=gas_nist,
    security_metric_type="security_equiv_bits",
    security_metric_value=float(sec_nist),
    gas_per_secure_bit=float((gas_nist / sec_nist) if (gas_nist and sec_nist) else 0.0),
    notes=note(gas_nist, sec_nist),
)

r2 = dict(common)
r2.update(
    bench_name=bench_evm,
    gas_verify=gas_evm,
    security_metric_type="security_equiv_bits",
    security_metric_value=float(sec_evm),
    gas_per_secure_bit=float((gas_evm / sec_evm) if (gas_evm and sec_evm) else 0.0),
    notes=note(gas_evm, sec_evm),
)

row1.parent.mkdir(parents=True, exist_ok=True)
row1.write_text(json.dumps(r1, indent=2) + "\n", encoding="utf-8")
row2.write_text(json.dumps(r2, indent=2) + "\n", encoding="utf-8")

print(f"[dil] wrote {row1}")
print(f"[dil] wrote {row2}")
PY

echo "[dil] wrote ${ROW1}"
echo "[dil] wrote ${ROW2}"

cd "${ROOT}"

if [[ "${RESET_DATA}" == "1" ]]; then
  echo "[dil] RESET_DATA=1 -> wiping data/results.*"
  rm -f data/results.jsonl data/results.csv
fi

echo "[dil] parse_bench -> append dataset row #1 (nist)"
python3 scripts/parse_bench.py "${ROW1}"

echo "[dil] parse_bench -> append dataset row #2 (evm)"
python3 scripts/parse_bench.py "${ROW2}"

echo "[dil] regenerate reports"
bash scripts/make_reports.sh

echo "[dil] done"
