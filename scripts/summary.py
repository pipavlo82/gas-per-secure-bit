#!/usr/bin/env python3
import csv, sys

path = sys.argv[1] if len(sys.argv) > 1 else "data/results.csv"
rows = list(csv.DictReader(open(path, newline="")))
rows.sort(key=lambda r: float(r["gas_per_secure_bit"]))

for r in rows:
    print(f'{r["scheme"]:10s} {r["bench_name"]:38s} gas={int(r["gas_verify"]):>9,d}  gas/bit={float(r["gas_per_secure_bit"]):>12,.3f}  repo={r["repo"]}@{r["commit"][:8]}')
