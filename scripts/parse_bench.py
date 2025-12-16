#!/usr/bin/env python3
import json, sys, csv, datetime, subprocess

def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"

def main():
    if len(sys.argv) < 2:
        print("Usage: parse_bench.py <jsonl_in_or_single_json>", file=sys.stderr)
        sys.exit(1)

    inp = sys.argv[1]
    commit = git_commit()
    ts = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

    # Accept either a path to a file, or a single JSON object string.
    rows = []
    try:
        with open(inp, "r", encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
    except FileNotFoundError:
        rows.append(json.loads(inp))

    # Normalize + compute
    out = []
    for r in rows:
        gas = int(r["gas_verify"])
        t = r["security_metric_type"]
        v = float(r["security_metric_value"])
        gp = gas / v if v != 0 else None

        out.append({
            "ts_utc": r.get("ts_utc", ts),
            "repo": r.get("repo", "gas-per-secure-bit"),
            "commit": r.get("commit", commit),
            "scheme": r["scheme"],
            "bench_name": r["bench_name"],
            "chain_profile": r.get("chain_profile", "unknown"),
            "gas_verify": gas,
            "security_metric_type": t,
            "security_metric_value": v,
            "gas_per_secure_bit": gp,
            "hash_profile": r.get("hash_profile", "unknown"),
            "notes": r.get("notes", "")
        })

    # Append JSONL
    with open("data/results.jsonl", "a", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")

    # Write CSV (full regen)
    with open("data/results.jsonl", "r", encoding="utf-8") as f:
        all_rows = [json.loads(line) for line in f if line.strip()]

    fields = ["ts_utc","repo","commit","scheme","bench_name","chain_profile","gas_verify",
              "security_metric_type","security_metric_value","gas_per_secure_bit","hash_profile","notes"]

    with open("data/results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k,"") for k in fields})

    print("Wrote data/results.jsonl and data/results.csv")

if __name__ == "__main__":
    main()
