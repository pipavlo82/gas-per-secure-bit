#!/usr/bin/env python3
import csv

path="data/results.csv"
rows=list(csv.DictReader(open(path, newline='', encoding='utf-8')))

latest={}
for r in rows:
    k=(r["repo"], r["bench_name"], r["chain_profile"])
    if k not in latest or r["ts_utc"] > latest[k]["ts_utc"]:
        latest[k]=r

for k in sorted(latest):
    r=latest[k]
    print(
        f'{r["ts_utc"]} '
        f'{r["repo"]} '
        f'{r["bench_name"]} '
        f'{r["chain_profile"]} '
        f'gas={r["gas_verify"]} '
        f'g/bit={r["gas_per_secure_bit"]}'
    )
