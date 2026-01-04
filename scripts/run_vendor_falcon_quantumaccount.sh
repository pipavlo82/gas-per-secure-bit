#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR_DIR="${ROOT}/vendors/QuantumAccount"

# Defaults: pinned vendor source (override via env if needed)
: "${QA_REPO_URL:=https://github.com/Cointrol-Limited/QuantumAccount.git}"
: "${QA_REF:=1970dcad8907c5dcb0df5ae51ea962b10fc3227b}"

# Confirmed Foundry test names in this vendor
: "${QA_TEST_GETHASH:=testQuantumAccountGetUserOpHashViaEntry}"
: "${QA_TEST_HANDLEOPS:=testQuantumAccountViaEntryPoint}"

# Dataset knobs
: "${CHAIN_PROFILE:=evm-l1}"
: "${SEC_BITS:=256}"          # Falcon-1024 normalization target
: "${RESET_DATA:=0}"

mkdir -p "${ROOT}/.tmp"
LOG_GETHASH="${ROOT}/.tmp/qa_getUserOpHash.log"
LOG_HANDLEOPS="${ROOT}/.tmp/qa_handleOps.log"
ROW1_JSON_FILE="${ROOT}/.tmp/qa_row_getUserOpHash.json"
ROW2_JSON_FILE="${ROOT}/.tmp/qa_row_handleOps.json"

if [[ ! -d "${VENDOR_DIR}/.git" ]]; then
  echo "[qa] cloning ${QA_REPO_URL} -> ${VENDOR_DIR}"
  git clone "${QA_REPO_URL}" "${VENDOR_DIR}"
fi

cd "${VENDOR_DIR}"
git fetch --all --tags
git checkout -f "${QA_REF}"
PINNED_COMMIT="$(git rev-parse HEAD)"

echo "[qa] pinned commit: ${PINNED_COMMIT}"
echo "[qa] repo path: vendors/QuantumAccount"

echo "[qa] updating submodules"
git submodule update --init --recursive

echo "[qa] running Foundry gas tests"
forge test --match-test "${QA_TEST_GETHASH}" -vv | tee "${LOG_GETHASH}"
forge test --match-test "${QA_TEST_HANDLEOPS}" -vv | tee "${LOG_HANDLEOPS}"

extract_gas() {
  local logfile="$1"
  local n
  n="$(grep -Eo '\(gas: [0-9]+\)' "${logfile}" | head -n1 | tr -cd '0-9' || true)"
  if [[ -z "${n}" ]]; then echo "0"; else echo "${n}"; fi
}

GAS_GETHASH="$(extract_gas "${LOG_GETHASH}")"
GAS_HANDLEOPS="$(extract_gas "${LOG_HANDLEOPS}")"

echo "[qa] gas getUserOpHash: ${GAS_GETHASH}"
echo "[qa] gas handleOps: ${GAS_HANDLEOPS}"

# Derived metrics (no newlines)
GPB256_GETHASH="$(python3 -c "gas=int('${GAS_GETHASH}'); print((gas/${SEC_BITS}) if gas else 0, end='')")"
GPB256_HANDLEOPS="$(python3 -c "gas=int('${GAS_HANDLEOPS}'); print((gas/${SEC_BITS}) if gas else 0, end='')")"
GPB_EFF128_HANDLEOPS="$(python3 -c "gas=int('${GAS_HANDLEOPS}'); print((gas/128) if gas else 0, end='')")"

NOTES_GETHASH="sec256=256 gpb256=${GPB256_GETHASH}"
NOTES_HANDLEOPS="sec256=256 gpb256=${GPB256_HANDLEOPS} weakest_link=erc4337_bundler_ecdsa eff128=128 gpb_eff=${GPB_EFF128_HANDLEOPS}"

cd "${ROOT}"

if [[ "${RESET_DATA}" == "1" ]]; then
  echo "[qa] RESET_DATA=1 -> wiping data/results.*"
  rm -f data/results.jsonl data/results.csv
fi

# Write two single-record JSON inputs in the schema parse_bench actually uses for results.csv:
# (gas_verify, security_metric_type/value, gas_per_secure_bit, surface_class, security_model, depends_on, provenance)
export PINNED_COMMIT CHAIN_PROFILE SEC_BITS GAS_GETHASH GAS_HANDLEOPS NOTES_GETHASH NOTES_HANDLEOPS ROW1_JSON_FILE ROW2_JSON_FILE

python3 - <<'PY'
import json, os
from pathlib import Path

pinned = os.environ["PINNED_COMMIT"]
chain_profile = os.environ["CHAIN_PROFILE"]
sec_bits = int(os.environ["SEC_BITS"])
gas_get = int(os.environ["GAS_GETHASH"])
gas_ops = int(os.environ["GAS_HANDLEOPS"])

def row(bench_name, surface_class, gas, notes, depends_on=""):
    gpbs = (gas / sec_bits) if (gas and sec_bits) else 0.0
    return {
        "repo": "QuantumAccount",
        "commit": pinned,
        "scheme": "falcon",
        "bench_name": bench_name,
        "chain_profile": chain_profile,

        # columns in results.csv
        "gas_verify": gas,
        "security_metric_type": "security_equiv_bits",
        "security_metric_value": float(sec_bits),
        "gas_per_secure_bit": float(gpbs),

        "hash_profile": "unknown",
        "security_model": "weakest-link" if depends_on else "standalone",
        "surface_class": surface_class,
        "notes": notes,
        "depends_on": depends_on,

        # single column in results.csv; encode full provenance tuple
        "provenance": f"QuantumAccount(path=vendors/QuantumAccount; commit={pinned}; bench={bench_name})",
    }

r1 = row(
    bench_name="falcon_getUserOpHash_via_entry",
    surface_class="aa::getUserOpHash",
    gas=gas_get,
    notes=os.environ["NOTES_GETHASH"],
    depends_on=""
)

r2 = row(
    bench_name="falcon_handleOps_userOp_e2e",
    surface_class="aa::handleOps",
    gas=gas_ops,
    notes=os.environ["NOTES_HANDLEOPS"],
    depends_on="erc4337_bundler_ecdsa"
)

p1 = Path(os.environ["ROW1_JSON_FILE"])
p2 = Path(os.environ["ROW2_JSON_FILE"])
p1.parent.mkdir(parents=True, exist_ok=True)
p1.write_text(json.dumps(r1) + "\n", encoding="utf-8")
p2.write_text(json.dumps(r2) + "\n", encoding="utf-8")

print("[qa] wrote", p1)
print("[qa] wrote", p2)
PY

# Prune any prior rows with same (repo,commit,scheme,bench_name) BEFORE append,
# so we don't rely on downstream dedup behavior.
python3 - <<'PY'
import json
from pathlib import Path

root = Path("/mnt/c/Users/msi/gas-per-secure-bit")
jsonl = root / "data" / "results.jsonl"
if not jsonl.exists():
    print("[qa] no existing data/results.jsonl -> skip prune")
    raise SystemExit(0)

bench_files = [
    root / ".tmp" / "qa_row_getUserOpHash.json",
    root / ".tmp" / "qa_row_handleOps.json",
]

targets = set()
for bf in bench_files:
    rec = json.loads(bf.read_text(encoding="utf-8"))
    targets.add((rec.get("repo"), rec.get("commit"), rec.get("scheme"), rec.get("bench_name")))

kept = []
for line in jsonl.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except Exception:
        kept.append(line)
        continue
    key = (r.get("repo"), r.get("commit"), r.get("scheme"), r.get("bench_name"))
    if key in targets:
        continue
    kept.append(json.dumps(r, ensure_ascii=False))

jsonl.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
print(f"[qa] pruned {len(targets)} target keys from data/results.jsonl")
PY

echo "[qa] parse_bench -> append dataset row #1 (getUserOpHash)"
python3 scripts/parse_bench.py "${ROW1_JSON_FILE}"

echo "[qa] parse_bench -> append dataset row #2 (handleOps)"
python3 scripts/parse_bench.py "${ROW2_JSON_FILE}"

echo "[qa] regenerate reports"
bash scripts/make_reports.sh

echo "[qa] done"
