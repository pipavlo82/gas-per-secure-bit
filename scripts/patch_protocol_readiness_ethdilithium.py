#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORT = os.path.join(ROOT, "reports", "protocol_readiness.md")
JSONL = os.path.join(ROOT, "data", "results.jsonl")

BEGIN = "<!-- ETHDILITHIUM_VENDOR_BEGIN -->"
END   = "<!-- ETHDILITHIUM_VENDOR_END -->"

TARGET_REPO = "ZKNoxHQ/ETHDILITHIUM"
TARGETS = [
    ("ethdilithium_eth_verify_log",  "dilithium", "verify (ETH mode, log)"),
    ("ethdilithium_nist_verify_log", "dilithium", "verify (NIST mode, log)"),
    ("ethdilithium_p256verify_log",  "p256",      "P-256 verify micro (log)"),
]

def parse_ts(s: str) -> datetime:
    # e.g. 2026-01-05T00:08:42Z
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)

def load_latest():
    latest = {}
    if not os.path.exists(JSONL):
        return latest
    with open(JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("repo") != TARGET_REPO:
                continue
            bn = r.get("bench_name")
            if bn not in {t[0] for t in TARGETS}:
                continue
            ts = r.get("ts_utc")
            if not ts:
                continue
            dt = parse_ts(ts)
            cur = latest.get(bn)
            if cur is None or dt > parse_ts(cur["ts_utc"]):
                latest[bn] = r
    return latest

def fmt_int(x):
    return f"{int(x):,}"

def fmt_float(x):
    # keep stable decimals like other tables
    if isinstance(x, int):
        return str(x)
    return f"{float(x):.6f}".rstrip("0").rstrip(".")

def build_block(latest):
    # Build markdown block content
    rows = []
    for bn, scheme, label in TARGETS:
        r = latest.get(bn)
        if not r:
            continue
        gas = r.get("gas_verify")
        lam = r.get("security_metric_value", 128.0)
        gpb = r.get("gas_per_secure_bit")
        prov = r.get("provenance", {}) or {}
        commit = prov.get("commit", r.get("commit", "unknown"))
        path = prov.get("path", "vendors/ETHDILITHIUM")

        # Notes: keep it minimal + explicit provenance
        note = r.get("notes", "")
        # keep notes short in table cell
        note = re.sub(r"\s+", " ", note).strip()
        if len(note) > 110:
            note = note[:107] + "..."

        rows.append({
            "bench": bn,
            "gas": gas,
            "lambda": lam,
            "gpb": gpb,
            "commit": commit,
            "path": path,
            "note": note,
            "scheme": scheme,
            "label": label,
        })

    lines = []
    lines.append(BEGIN)
    lines.append("")
    lines.append("### Vendor snapshot: ZKNoxHQ/ETHDILITHIUM")
    lines.append("")
    lines.append("- Source: `ZKNoxHQ/ETHDILITHIUM` (pinned by commit)")
    lines.append("- Runner: `scripts/run_vendor_ethdilithium.sh` (log-extracted `Gas used:`; excludes FFI-based tests like `testVerifyShorter()`)")
    lines.append("")
    lines.append("| bench_name | scheme | description | gas_verify | security_metric | value | gas/bit | vendor_commit | vendor_path | notes |")
    lines.append("|---|---:|---|---:|---|---:|---:|---|---|---|")

    for rr in rows:
        gas = rr["gas"]
        gpb = rr["gpb"]
        lines.append(
            f"| `{rr['bench']}` | `{rr['scheme']}` | {rr['label']} | "
            f"{fmt_int(gas)} | `lambda_eff` | {fmt_float(rr['lambda'])} | {fmt_float(gpb)} | "
            f"`{rr['commit'][:12]}` | `{rr['path']}` | {rr['note']} |"
        )

    lines.append("")
    lines.append("Notes:")
    lines.append("- `lambda_eff=128` here is a budgeting denominator (not a finalized security-equivalence mapping for Dilithium variants).")
    lines.append("- If/when we normalize Dilithium to `security_equiv_bits`, we will add `secXXX=...` and `gpbXXX=...` annotations similar to MLDSA65.")
    lines.append("")
    lines.append(END)
    return "\n".join(lines) + "\n"

def patch_file(block: str):
    with open(REPORT, "r", encoding="utf-8") as f:
        s = f.read()

    if BEGIN in s and END in s:
        s2 = re.sub(
            re.escape(BEGIN) + r".*?" + re.escape(END),
            block.strip(),
            s,
            flags=re.DOTALL
        )
        s2 = s2 + ("\n" if not s2.endswith("\n") else "")
    else:
        # If markers not present, append block to end of file.
        if not s.endswith("\n"):
            s += "\n"
        s2 = s + "\n" + block

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(s2)

def main():
    latest = load_latest()
    block = build_block(latest)
    patch_file(block)

if __name__ == "__main__":
    main()
