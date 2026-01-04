#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

JSONL="data/results.jsonl"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 1; }; }
need_cmd python3
need_cmd forge
need_cmd grep
need_cmd tee

# Measure gas for a contract test suite.
# Prefer log-isolated marker lines:
#   "<marker> gas: <N>"  OR  "<marker> gas= <N>"
# If marker is missing, fallback to harness "(gas: <N>)" and emit WARN.
#
# Output: "<mode>:<gas>" where mode ∈ {log,harness}
measure_gas() {
  local contract="$1"
  local marker="$2"
  local out="/tmp/${contract}.out"

  forge test --match-contract "$contract" -vv 2>&1 | tee "$out" >/dev/null

  local g=""
  local mode="log"

  if [[ -n "${marker}" ]]; then
    # Marker can contain '::' etc. We allow any chars until 'gas:' or 'gas='
    g="$(grep -oP "${marker}.*?(?:gas:|gas=)\s*\K[0-9]+" "$out" | head -n1 || true)"
  fi

  if [[ -z "${g}" ]]; then
    # Fallback to harness gas (includes setup/overhead).
    g="$(grep -oP '\(gas:\s*\K[0-9]+' "$out" | head -n1 || true)"
    mode="harness"
  fi

  if [[ -z "${g}" ]]; then
    echo "failed to parse gas for contract=$contract marker=$marker (see $out)" >&2
    echo "hint: either emit a log line '<marker> gas: <N>' OR ensure Forge prints '(gas: N)'." >&2
    exit 1
  fi

  if [[ "${mode}" == "harness" && -n "${marker}" ]]; then
    echo "WARN: marker not found for contract=$contract marker=$marker; falling back to harness (gas: ${g})" >&2
  fi

  echo "${mode}:${g}"
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

# --- Measurements (prefer log markers; fallback ok) ---

echo "[1/6] Measure gas: RANDAO (mix)"
RANDAO_RES="$(measure_gas ProtocolRandaoSurface_Gas_Test "randao::l1_randao_mix_surface")"
RANDAO_MODE="${RANDAO_RES%%:*}"
RANDAO_GAS="${RANDAO_RES#*:}"
echo "RANDAO_GAS=$RANDAO_GAS (mode=$RANDAO_MODE)"

echo "[2/6] Measure gas: Relay attestation"
RELAY_RES="$(measure_gas ProtocolRelayAttestationSurface_Gas_Test "attestation::relay_attestation_surface")"
RELAY_MODE="${RELAY_RES%%:*}"
RELAY_GAS="${RELAY_RES#*:}"
echo "RELAY_GAS=$RELAY_GAS (mode=$RELAY_MODE)"

echo "[3/6] Measure gas: DAS sample verify (512B)"
DAS_RES="$(measure_gas ProtocolDASSampleSurface_Gas_Test "das::verify_sample_512b_surface")"
DAS_MODE="${DAS_RES%%:*}"
DAS_GAS="${DAS_RES#*:}"
echo "DAS_GAS=$DAS_GAS (mode=$DAS_MODE)"

echo "[4/6] Measure gas: RANDAO mix for sample selection"
RANDAO_SAMPLING_RES="$(measure_gas ProtocolRandaoSamplingSurface_Gas_Test "randao::mix_for_sample_selection_surface")"
RANDAO_SAMPLING_MODE="${RANDAO_SAMPLING_RES%%:*}"
RANDAO_SAMPLING_GAS="${RANDAO_SAMPLING_RES#*:}"
echo "RANDAO_SAMPLING_GAS=$RANDAO_SAMPLING_GAS (mode=$RANDAO_SAMPLING_MODE)"

echo "[5/6] Replace semantics: prune old records (regardless of commit)"
prune_records "randao" "l1_randao_mix_surface"
prune_records "attestation" "relay_attestation_surface"
prune_records "das" "verify_sample_512b_surface"
prune_records "randao" "mix_for_sample_selection_surface"

echo "[6/6] Append fresh measured records via parse_bench.py"

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
  "notes": "Measured via Foundry (${RANDAO_MODE}): ProtocolRandaoSurface_Gas_Test.test_l1_randao_mix_surface_gas() => ${RANDAO_GAS} gas. If mode=harness, this includes test overhead because the marker log line was not found. Denominator is H_min (min-entropy bits) under explicit threat model; H_min=32 is a declared placeholder until model is pinned down."
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
  "notes": "Measured via Foundry (${RELAY_MODE}): ProtocolRelayAttestationSurface_Gas_Test.test_relay_attestation_surface_gas() => ${RELAY_GAS} gas. If mode=harness, this includes test overhead because the marker log line was not found. Denominator is H_min under explicit threat model; H_min=128 is a declared placeholder until model is pinned down."
}
JSON
)"

python3 scripts/parse_bench.py "$(cat <<JSON
{
  "scheme": "das",
  "bench_name": "verify_sample_512b_surface",
  "chain_profile": "EVM/L1",
  "gas_verify": ${DAS_GAS},
  "security_metric_type": "das_sample_bits",
  "security_metric_value": 4096,
  "hash_profile": "protocol",
  "surface_class": "DataAvailabilitySurface",
  "security_model": "raw",
  "notes": "Measured via Foundry (${DAS_MODE}): ProtocolDASSampleSurface_Gas_Test.test_gas_das_verify_sample_512b_surface() => ${DAS_GAS} gas. Denominator is sample size bits (512B = 4096 bits). Protocol surface for DA sampling/verification cost budgeting."
}
JSON
)"

python3 scripts/parse_bench.py "$(cat <<JSON
{
  "scheme": "randao",
  "bench_name": "mix_for_sample_selection_surface",
  "chain_profile": "EVM/L1",
  "gas_verify": ${RANDAO_SAMPLING_GAS},
  "security_metric_type": "H_min",
  "security_metric_value": 32,
  "hash_profile": "protocol",
  "surface_class": "EntropySurface",
  "security_model": "raw",
  "notes": "Measured via Foundry (${RANDAO_SAMPLING_MODE}): ProtocolRandaoSamplingSurface_Gas_Test.test_gas_randao_mix_for_sample_selection_surface() => ${RANDAO_SAMPLING_GAS} gas. Intended use: selecting random DAS samples. Denominator H_min=32 is a declared placeholder until the threat model is pinned down."
}
JSON
)"

echo "[post] Regenerate reports"
bash scripts/make_reports.sh

echo
echo "OK. Updated:"
echo " - data/results.jsonl"
echo " - data/results.csv"
echo " - reports/*"
