#!/usr/bin/env bash
set -euo pipefail

echo "[pre] Dedup data/results.jsonl (scheme,bench_name,repo,commit)"
python3 scripts/dedup_results.py || true

echo "[0/5] Rebuild data/results.csv from data/results.jsonl"
python3 scripts/parse_bench.py --regen data/results.jsonl

echo "[1/5] Sanity: required files"
test -f data/results.jsonl
test -f scripts/parse_bench.py

echo "[2/5] Sanity: JSONL must be one-JSON-per-line"
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

echo "[3/5] Sanity: uniqueness of (scheme, bench_name, repo, commit, chain_profile, security_metric_type)"
python3 - <<'PY'
import csv,sys
rows=list(csv.DictReader(open("data/results.csv","r",encoding="utf-8")))
seen={}
dups=[]
for r in rows:
    
    k=(r.get("scheme",""), r.get("bench_name",""), r.get("repo",""), r.get("commit",""), r.get("chain_profile",""), r.get("security_metric_type",""))
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

