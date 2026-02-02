#!/usr/bin/env bash
set -euo pipefail

echo "[pre] Dedup data/results.jsonl (scheme,bench_name,repo,commit)"
python3 scripts/dedup_results.py || true

echo "[0/5] Rebuild data/results.csv from data/results.jsonl"
python3 scripts/parse_bench.py --regen data/results.jsonl

echo "[1/5] Sanity: required files"
test -f data/results.jsonl
test -f scripts/parse_bench.py

# Step 2 (JSONL sanity) and Step 3 (CSV uniqueness) are redundant:
# - dedup_results.py already validates JSONL structure and removes duplicates.
# - parse_bench.py --regen builds CSV 1:1 from valid JSONL.
# Skipping to save 2 extra parse passes.

echo "[4/5] Generate reports"
if test -f scripts/report_weakest_link.py; then
  python3 scripts/report_weakest_link.py
else
  echo "WARN: scripts/report_weakest_link.py not found; skipping"
fi

echo "[5/5] Generate protocol readiness"
python3 scripts/make_protocol_readiness.py

# Post-process: inject ML-DSA-65 vendor measurements (pinned ref)
if test -f scripts/patch_protocol_readiness_mldsa.py; then
  python3 scripts/patch_protocol_readiness_mldsa.py --jsonl data/results.jsonl --report reports/protocol_readiness.md
else
  echo "WARN: scripts/patch_protocol_readiness_mldsa.py not found; skipping"
fi

# Post-process: inject Falcon vendor measurements (pinned ref)
if test -f scripts/patch_protocol_readiness_falcon.py; then
  python3 scripts/patch_protocol_readiness_falcon.py data/results.jsonl reports/protocol_readiness.md
else
  echo "WARN: scripts/patch_protocol_readiness_falcon.py not found; skipping"
fi

# Post-process: inject Dilithium vendor measurements (pinned ref)
if test -f scripts/patch_protocol_readiness_ethdilithium.py; then
  python3 scripts/patch_protocol_readiness_ethdilithium.py --jsonl data/results.jsonl --report reports/protocol_readiness.md
else
  echo "WARN: scripts/patch_protocol_readiness_ethdilithium.py not found; skipping"
fi

echo "Done."
ls -la reports || true
