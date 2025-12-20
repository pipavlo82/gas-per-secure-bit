#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

JSONL="data/results.jsonl"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 1; }; }
need_cmd python3
need_cmd forge
need_cmd grep

measure_gas() {
  local contract="$1"
  local out="/tmp/${contract}.out"
  forge test --match-contract "$contract" -vv 2>&1 | tee "$out" >/dev/null
  local g
  g="$(grep -oP '\(gas:\s*\K[0-9]+' "$out" | head -n1 || true)"
  if [[ -z "${g}" ]]; then
    echo "failed to parse gas for $contract (see $out)" >&2
    exit 1
  fi
  echo "$g"
}

prune_records() {
  local scheme="$1"
  local bench="$2"

  # Remove *all* previous records for (repo=gas-per-secure-bit, scheme, bench_name),
  # regardless of commit/ts. This is the "replace" semantics.
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
        r.get("repo") == "gas-per-secure-bit"
        and r.get("scheme") == scheme
        and r.get("bench_name") == bench
    ):
        removed += 1
        continue

    out_lines.append(json.dumps(r, ensure_ascii=False))

path.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
print(f"prune: removed {removed} records for {scheme}::{bench}", file=sys.stderr)
PY
}

echo "[1/5] Measure gas: RANDAO"
RANDAO_GAS="$(measure_gas ProtocolRandaoSurface_Gas_Test)"
echo "RANDAO_GAS=$RANDAO_GAS"

echo "[2/5] Measure gas: Relay attestation"
RELAY_GAS="$(measure_gas ProtocolRelayAttestationSurface_Gas_Test)"
echo "RELAY_GAS=$RELAY_GAS"

echo "[3/5] Replace semantics: prune old records (regardless of commit)"
prune_records "randao" "l1_randao_mix_surface"
prune_records "attestation" "relay_attestation_surface"

echo "[4/5] Append fresh measured records via parse_bench.py"
python3 scripts/parse_bench.py "$(cat <<JSON
{
  "scheme": "randao",
  "bench_name": "l1_randao_mix_surface",
  "chain_profile": "EVM/L1",
  "gas_verify": ${RANDAO_GAS},
  "security_metric_type": "H_min",
  "security_metric_value": 32,
  "hash_profile": "protocol",
  "surface_class": "EntropySurface",
  "security_model": "raw",
  "notes": "Measured via Foundry: ProtocolRandaoSurface_Gas_Test.test_l1_randao_mix_surface_gas() => (gas: ${RANDAO_GAS}). Denominator is H_min (min-entropy bits) under explicit threat model; H_min=32 is a declared placeholder until model is pinned down."
}
JSON
)"

python3 scripts/parse_bench.py "$(cat <<JSON
{
  "scheme": "attestation",
  "bench_name": "relay_attestation_surface",
  "chain_profile": "EVM/L1",
  "gas_verify": ${RELAY_GAS},
  "security_metric_type": "H_min",
  "security_metric_value": 128,
  "hash_profile": "protocol",
  "surface_class": "EntropySurface",
  "security_model": "raw",
  "notes": "Measured via Foundry: ProtocolRelayAttestationSurface_Gas_Test.test_relay_attestation_surface_gas() => (gas: ${RELAY_GAS}). Denominator is H_min under explicit threat model; H_min=128 is a declared placeholder until model is pinned down."
}
JSON
)"

echo "[5/5] Regenerate reports"
./scripts/make_reports.sh

echo
echo "OK. Updated:"
echo " - data/results.jsonl"
echo " - data/results.csv"
echo " - reports/*"
