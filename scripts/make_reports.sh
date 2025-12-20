#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Sanity: required files"
test -f data/results.jsonl
test -f scripts/parse_bench.py

echo "[2/4] Sanity: JSONL must be one-JSON-per-line"
python3 - <<'PY'
import json,sys
bad=0
for i,line in enumerate(open("data/results.jsonl","r",encoding="utf-8"),1):
    line=line.strip()
    if not line: 
        continue
    try:
        json.loads(line)
    except Exception as e:
        bad+=1
        print(f"BAD JSONL line {i}: {e}", file=sys.stderr)
if bad:
    sys.exit(2)
print("OK: jsonl parses")
PY

echo "[3/4] Sanity: uniqueness of (scheme, bench_name, repo, commit)"
python3 - <<'PY'
import csv,sys
rows=list(csv.DictReader(open("data/results.csv","r",encoding="utf-8")))
seen={}
dups=[]
for r in rows:
    k=(r.get("scheme",""), r.get("bench_name",""), r.get("repo",""), r.get("commit",""))
    seen[k]=seen.get(k,0)+1
for k,c in seen.items():
    if c>1:
        dups.append((c,k))
if dups:
    dups.sort(reverse=True)
    print("DUPLICATES:", file=sys.stderr)
    for c,k in dups[:50]:
        print(c,k, file=sys.stderr)
    sys.exit(3)
print("OK: no duplicates")
PY

echo "[4/4] Generate reports"
if test -f scripts/report_weakest_link.py; then
  python3 scripts/report_weakest_link.py
else
  echo "WARN: scripts/report_weakest_link.py not found; skipping"
fi

if test -f scripts/report_protocol_readiness.py; then
  python3 scripts/report_protocol_readiness.py
else
  echo "INFO: scripts/report_protocol_readiness.py not found; protocol report is static (reports/protocol_readiness.md)"
fi

echo "Done."
ls -la reports || true

python3 scripts/make_protocol_readiness.py
