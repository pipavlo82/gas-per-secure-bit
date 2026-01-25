#!/usr/bin/env python3
import json
from pathlib import Path


KEY_FIELDS = ("scheme", "bench_name", "repo", "commit", "chain_profile", "security_metric_type")

def key_of(r: dict):
    return tuple(r.get(k) for k in KEY_FIELDS)

def main():
    p = Path("data/results.jsonl")
    if not p.exists():
        return
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))

    
# keep LAST occurrence per (scheme, bench_name, repo, commit, chain_profile, security_metric_type)
    seen = {}
    for i, r in enumerate(rows):
        seen[key_of(r)] = i

    keep_idx = set(seen.values())
    out = [rows[i] for i in range(len(rows)) if i in keep_idx]

    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
