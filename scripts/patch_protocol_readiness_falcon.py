#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BEGIN = "<!-- FALCON_VENDOR_BEGIN -->"
END   = "<!-- FALCON_VENDOR_END -->"

TARGETS = [
    ("falcon", "falcon_getUserOpHash_via_entry", "QuantumAccount"),
    ("falcon", "falcon_handleOps_userOp_e2e", "QuantumAccount"),
]

def load_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows

def pick_latest(rows, scheme, bench_name, repo):
    cand = [r for r in rows
            if r.get("scheme") == scheme
            and r.get("bench_name") == bench_name
            and r.get("repo") == repo]
    if not cand:
        return None
    # ts_utc is ISO; lexicographic sort OK
    cand.sort(key=lambda r: r.get("ts_utc", ""))
    return cand[-1]

def fmt_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        try:
            return f"{int(float(x)):,}"
        except Exception:
            return str(x)

def fmt_float(x):
    try:
        v = float(x)
        s = f"{v:.10f}".rstrip("0").rstrip(".")
        return s if s else "0"
    except Exception:
        return str(x)

def short_commit(c):
    c = c or ""
    return c[:12]

def render_block(picked):
    lines = []
    lines.append("### Falcon vendor (QuantumAccount) — pinned ref")
    lines.append("")
    lines.append("| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |")
    lines.append("|---|---:|---|---:|---:|---|---|---|")

    for r in picked:
        if r is None:
            lines.append("| _missing_ | - | - | - | - | - | - | - |")
            continue

        bench = r.get("bench_name", "")
        gas = fmt_int(r.get("gas_verify", 0))
        smt = r.get("security_metric_type", "unknown")
        bits = fmt_float(r.get("security_metric_value", 0.0))
        gpb = fmt_float(r.get("gas_per_secure_bit", 0.0))
        repo = r.get("repo", "")
        commit = short_commit(r.get("commit", ""))
        sec_model = r.get("security_model", "")
        notes = r.get("notes", "")

        lines.append(
            f"| `{bench}` | {gas} | `{smt}` | {bits} | {gpb} | `{repo}`@`{commit}` | `{sec_model}` | {notes} |"
        )

    lines.append("")
    lines.append("Notes:")
    lines.append("- `falcon_getUserOpHash_via_entry` measures the EntryPoint hashing surface (not end-to-end AA execution).")
    lines.append("- `falcon_handleOps_userOp_e2e` measures an end-to-end `handleOps()` flow, including ERC-4337 surface overhead; treat as a protocol-surface upper bound.")
    lines.append("- Normalization in this repo uses `security_equiv_bits = 256` for Falcon-1024 (Cat5-style denominator).")
    return "\n".join(lines)

def patch(md_text: str, block_text: str) -> str:
    if BEGIN in md_text and END in md_text:
        pre = md_text.split(BEGIN)[0]
        post = md_text.split(END)[1]
        return pre + BEGIN + "\n" + block_text + "\n" + END + post
    return md_text.rstrip() + "\n\n" + BEGIN + "\n" + block_text + "\n" + END + "\n"

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <data/results.jsonl> <reports/protocol_readiness.md>", file=sys.stderr)
        return 2

    jsonl_path = Path(sys.argv[1])
    md_path = Path(sys.argv[2])

    rows = load_jsonl(jsonl_path)
    picked = [pick_latest(rows, s, b, repo) for (s, b, repo) in TARGETS]
    block = render_block(picked)

    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    md_path.write_text(patch(md_text, block), encoding="utf-8")
    print(f"Wrote {md_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
