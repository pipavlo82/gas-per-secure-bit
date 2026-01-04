#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 1; }; }
need_cmd python3
need_cmd git
need_cmd forge
need_cmd rg
need_cmd tee

QA_DIR="vendors/QuantumAccount"
JSONL="data/results.jsonl"

# Optional: allow pinning via env
QA_REF="${QA_REF:-1970dcad8907c5dcb0df5ae51ea962b10fc3227b}"

echo "[0/7] Enter vendor repo: $QA_DIR"
cd "$QA_DIR"

echo "[1/7] Pin QuantumAccount ref: $QA_REF"
git fetch --all -q || true
git checkout -q "$QA_REF"

QA_REPO_URL="$(git remote get-url origin 2>/dev/null || echo "vendors/QuantumAccount")"
QA_COMMIT="$(git rev-parse HEAD)"
echo "QA_REPO_URL=$QA_REPO_URL"
echo "QA_COMMIT=$QA_COMMIT"

# Parse a log-isolated gas number from Forge output.
#
# Supports BOTH formats:
#   "<marker> gas: <N>"
#   "<marker>: <N>"
#
# Example seen in QuantumAccount:
#   "gas_falcon_verify: 10336055"
measure_log_gas_match_test() {
  local match_test="$1"
  local marker="$2"
  local out="/tmp/qa_${match_test}.out"

  forge test --match-test "$match_test" -vv 2>&1 | tee "$out" >/dev/null

  local g=""

  # Try: "<marker> gas: <N>"
  g="$(rg -o "${marker}\s+gas:\s*[0-9]+" "$out" | head -n1 | rg -o "[0-9]+$" || true)"

  # Try: "<marker>: <N>" (QuantumAccount style)
  if [[ -z "${g}" ]]; then
    g="$(rg -o "${marker}:\s*[0-9]+" "$out" | head -n1 | rg -o "[0-9]+$" || true)"
  fi

  if [[ -z "${g}" ]]; then
    echo "failed to parse LOG gas for test=$match_test marker=$marker (see $out)" >&2
    echo "hint: ensure the test prints either:" >&2
    echo "  '<marker> gas: <N>'  OR  '<marker>: <N>'" >&2
    echo "---- Logs excerpt ----" >&2
    sed -n '/Logs:/,$p' "$out" | sed -n '1,120p' >&2 || true
    exit 1
  fi

  echo "$g"
}

echo "[2/7] Measure Falcon verifySignature (log-isolated)"
# Observed logs: "gas_falcon_verify: <N>"
FALCON_VERIFY_GAS="$(measure_log_gas_match_test test_falcon_verify_gas_log "gas_falcon_verify")"
echo "FALCON_VERIFY_GAS=$FALCON_VERIFY_GAS"

echo "[3/7] Measure validateUserOp (log-isolated)"
# We haven't seen the exact marker yet; likely similar: "gas_validateUserOp: <N>"
QA_VALIDATEUSEROP_GAS="$(measure_log_gas_match_test test_validateUserOp_gas_log "gas_validateUserOp")"
echo "QA_VALIDATEUSEROP_GAS=$QA_VALIDATEUSEROP_GAS"

echo "[4/7] Return to root"
cd "$ROOT"

prune_records() {
  local scheme="$1"
  local bench="$2"
  python3 - "$JSONL" "$scheme" "$bench" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
scheme = sys.argv[2]
bench  = sys.argv[3]

if not path.exists():
    sys.exit(0)

out_lines = []
removed = 0

for line in path.read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if not s:
        continue
    try:
        r = json.loads(s)
    except Exception:
        out_lines.append(line)
        continue

    if (
        r.get("scheme") == scheme
        and r.get("bench_name") == bench
        and r.get("repo") == "QuantumAccount"
    ):
        removed += 1
        continue

    out_lines.append(json.dumps(r, ensure_ascii=False))

path.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
print(f"prune: removed {removed} records for QuantumAccount::{scheme}::{bench}", file=sys.stderr)
PY
}

echo "[5/7] Replace semantics: prune old Falcon vendor records (repo=QuantumAccount)"
prune_records "falcon" "falcon_verifySignature_log"
prune_records "falcon" "qa_validateUserOp_userop_log"

echo "[6/7] Append fresh vendor records via parse_bench.py (with provenance override)"

python3 scripts/parse_bench.py "$(cat <<JSON
{
  "repo": "QuantumAccount",
  "commit": "${QA_COMMIT}",
  "path": "${QA_REPO_URL} (ref=${QA_REF})",
  "scheme": "falcon",
  "bench_name": "falcon_verifySignature_log",
  "chain_profile": "EVM/L1",
  "gas_verify": ${FALCON_VERIFY_GAS},
  "security_metric_type": "security_equiv_bits",
  "security_metric_value": 256,
  "hash_profile": "vendor",
  "surface_class": "SignatureVerify",
  "security_model": "raw",
  "notes": "Vendor: QuantumAccount pinned (ref=${QA_REF}). Parsed from Foundry logs: test_falcon_verify_gas_log => 'gas_falcon_verify: <N>' (log-isolated)."
}
JSON
)"

python3 scripts/parse_bench.py "$(cat <<JSON
{
  "repo": "QuantumAccount",
  "commit": "${QA_COMMIT}",
  "path": "${QA_REPO_URL} (ref=${QA_REF})",
  "scheme": "falcon",
  "bench_name": "qa_validateUserOp_userop_log",
  "chain_profile": "EVM/L1",
  "gas_verify": ${QA_VALIDATEUSEROP_GAS},
  "security_metric_type": "security_equiv_bits",
  "security_metric_value": 256,
  "hash_profile": "vendor",
  "surface_class": "AA/ValidateUserOp",
  "security_model": "raw",
  "notes": "Vendor: QuantumAccount pinned (ref=${QA_REF}). Parsed from Foundry logs: test_validateUserOp_gas_log => 'gas_validateUserOp: <N>' (log-isolated)."
}
JSON
)"

echo "[7/7] Regenerate reports"
bash scripts/make_reports.sh

echo
echo "OK. Updated:"
echo " - data/results.jsonl"
echo " - data/results.csv"
echo " - reports/*"
