#!/usr/bin/env python3
import json
import sys
from pathlib import Path

KEY_FIELDS = ("scheme", "bench_name", "repo", "commit", "chain_profile", "security_metric_type")

def key_of(r: dict):
    return tuple(r.get(k) for k in KEY_FIELDS)

def main():
    p = Path("data/results.jsonl")
    if not p.exists():
        return

    lines = []
    
    # Track if we see any empty lines or bad lines that we skip, implying we should rewrite
    saw_skippable_lines = False
    total_lines_read = 0

    with p.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            total_lines_read += 1
            s = line.strip()
            if not s:
                saw_skippable_lines = True
                continue
            try:
                obj = json.loads(s)
            except Exception:
                print(f"WARN: skipping invalid JSON line {i+1}", file=sys.stderr)
                saw_skippable_lines = True
                continue

            lines.append((s, obj))

    # Identify indices to keep (last occurrence per key)
    seen = {}
    for idx, (s, obj) in enumerate(lines):
        k = key_of(obj)
        seen[k] = idx # overwrite with latest index

    keep_indices = set(seen.values())

    # Write if:
    # 1. We found duplicates (len(keep_indices) < len(lines))
    # 2. We skipped lines (saw_skippable_lines) - e.g. empty lines
    if len(keep_indices) == len(lines) and not saw_skippable_lines:
        # print("No duplicates or cleanup needed.", file=sys.stderr)
        return

    # print(f"Dedup: keeping {len(keep_indices)}/{len(lines)} records (read {total_lines_read} lines)", file=sys.stderr)

    output_lines = [lines[i][0] for i in sorted(keep_indices)]

    # Atomic write to avoid corruption
    temp_p = p.with_suffix(".tmp")
    try:
        with temp_p.open("w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")
        temp_p.replace(p)
    except Exception as e:
        if temp_p.exists():
            temp_p.unlink()
        raise e

if __name__ == "__main__":
    main()
