#!/usr/bin/env bash
set -euo pipefail

# Integration test for the pipeline

echo "Running pipeline integration test..."

# 1. Backup data
cp data/results.jsonl data/results.jsonl.bak
cp data/results.csv data/results.csv.bak

function cleanup {
  mv data/results.jsonl.bak data/results.jsonl
  mv data/results.csv.bak data/results.csv
  echo "Restored data."
}
trap cleanup EXIT

# 2. Run make_reports.sh
bash scripts/make_reports.sh

# 3. Add a test entry
echo "Adding test entry..."
python3 scripts/parse_bench.py '{"scheme":"test_integ","bench_name":"bench1","gas":100}'

# Verify it is in JSONL and CSV
if ! grep -q "test_integ" data/results.jsonl; then
  echo "FAIL: test_integ not in JSONL"
  exit 1
fi
if ! grep -q "test_integ" data/results.csv; then
  echo "FAIL: test_integ not in CSV"
  exit 1
fi

# 4. Run dedup (should keep it)
python3 scripts/dedup_results.py
if ! grep -q "test_integ" data/results.jsonl; then
  echo "FAIL: test_integ lost after dedup"
  exit 1
fi

# 5. Add duplicate
echo "Adding duplicate..."
# We simulate a duplicate by appending the same line again manually or via parse_bench
# parse_bench.py appends, so running it again adds a duplicate
python3 scripts/parse_bench.py '{"scheme":"test_integ","bench_name":"bench1","gas":100}'

# Verify we have 2
count=$(grep -c "test_integ" data/results.jsonl)
if [ "$count" -ne 2 ]; then
  echo "FAIL: Expected 2 copies, got $count"
  exit 1
fi

# 6. Run dedup (should remove one)
echo "Running dedup to clean..."
python3 scripts/dedup_results.py

count=$(grep -c "test_integ" data/results.jsonl)
if [ "$count" -ne 1 ]; then
  echo "FAIL: Expected 1 copy after dedup, got $count"
  exit 1
fi

echo "PASS: Pipeline integration test passed."
