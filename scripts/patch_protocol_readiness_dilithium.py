#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "results.csv"
MD_PATH = ROOT / "reports" / "protocol_readiness.md"

BEGIN = "<!-- DILITHIUM_VENDOR_BEGIN -->"
END = "<!-- DILITHIUM_VENDOR_END -->"

TARGET = [
    ("dilithium", "dilithium_verify_nistkat"),
    ("ethdilithium", "ethdilithium_verify_evmfriendly"),
]

def _latest_row(rows, scheme, bench):
    # pick latest by ts_utc lexicographically (ISO8601)
    cand = [r for r in rows if r.get("scheme") == scheme and r.get("bench_name") == bench and r.get("repo") == "ZKNoxHQ/ETHDILITHIUM"]
    if not cand:
        return None
    cand.sort(key=lambda r: r.get("ts_utc",""))
    return cand[-1]

def main():
    if not CSV_PATH.exists() or not MD_PATH.exists():
        raise SystemExit("missing results.csv or protocol_readiness.md; run scripts/make_reports.sh first")

    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    got = []
    for scheme, bench in TARGET:
        r = _latest_row(rows, scheme, bench)
        if r is not None:
            got.append(r)

    # Build block
    lines = []
    lines.append(BEGIN)
    lines.append("### Dilithium vendor (ZKNoxHQ/ETHDILITHIUM) — pinned ref")
    lines.append("")
    lines.append("| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |")
    lines.append("|---|---:|---|---:|---:|---|---|---|")

    if not got:
        lines.append("| _(missing)_ | 0 | `security_equiv_bits` | 0 | 0 | `ZKNoxHQ/ETHDILITHIUM`@`(none)` | `standalone` | run scripts/run_vendor_dilithium_ethdilithium.sh |")
    else:
        for r in got:
            bench = r["bench_name"]
            gas = int(float(r["gas_verify"]))
            smt = r["security_metric_type"]
            bits = int(float(r["security_metric_value"])) if r["security_metric_value"] else 0
            gpb = r["gas_per_secure_bit"]
            repo = r["repo"]
            commit = r["commit"][:11]
            sec_model = r.get("security_model","standalone")
            notes = r.get("notes","")
            lines.append(f"| `{bench}` | {gas:,} | `{smt}` | {bits} | {gpb} | `{repo}`@`{commit}` | `{sec_model}` | {notes} |")

    lines.append("")
    lines.append("Notes:")
    lines.append("- `dilithium_verify_nistkat` is the NIST-shape verifier in the vendor repo.")
    lines.append("- `ethdilithium_verify_evmfriendly` is the EVM-friendly variant in the same vendor repo.")
    lines.append("- Denominator here uses `security_equiv_bits` (override SEC_BITS_* in the runner if you confirm a different category).")
    lines.append(END)

    block = "\n".join(lines) + "\n"

    md = MD_PATH.read_text(encoding="utf-8")
    if BEGIN in md and END in md:
        pre = md.split(BEGIN)[0]
        post = md.split(END)[1]
        md2 = pre + block + post
    else:
        # append at end if markers absent
        md2 = md.rstrip() + "\n\n" + block

    MD_PATH.write_text(md2, encoding="utf-8")
    print(f"[patch] wrote {MD_PATH}")

if __name__ == "__main__":
    main()
