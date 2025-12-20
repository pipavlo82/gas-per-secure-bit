#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
JSONL = ROOT / "data" / "results.jsonl"
CSV = ROOT / "data" / "results.csv"

PREFERRED = [
    "ts_utc",
    "repo", "commit", "scheme", "bench_name", "chain_profile",
    "gas_verify", "gas_surface", "gas",
    "security_metric_type", "security_metric_value",
    "gas_per_secure_bit",
    "hash_profile", "security_model", "surface_class",
    "notes", "depends_on",
]

def _normalize_depends_on(o: Dict[str, Any]) -> None:
    dep = o.get("depends_on")
    if isinstance(dep, list):
        o["depends_on"] = ";".join(str(x) for x in dep)
    elif dep is None:
        o["depends_on"] = ""
    else:
        o["depends_on"] = str(dep)

def main() -> None:
    if not JSONL.exists():
        raise SystemExit(f"Missing {JSONL}")

    rows: List[Dict[str, Any]] = []
    all_keys: Set[str] = set()

    for i, line in enumerate(JSONL.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception as e:
            raise SystemExit(f"Bad JSON on line {i}: {e}") from e

        if not isinstance(o, dict):
            raise SystemExit(f"JSONL line {i} is not an object")

        _normalize_depends_on(o)
        rows.append(o)
        all_keys |= set(o.keys())

    rest = sorted(k for k in all_keys if k not in PREFERRED)
    header = [k for k in PREFERRED if k in all_keys] + rest

    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for o in rows:
            w.writerow({k: o.get(k, "") for k in header})

    print(f"WROTE {CSV} cols={len(header)} rows={len(rows)}")

if __name__ == "__main__":
    main()
