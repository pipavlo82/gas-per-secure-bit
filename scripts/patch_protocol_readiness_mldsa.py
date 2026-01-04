#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BEGIN = "<!-- MLDSA65_VENDOR_BEGIN -->"
END   = "<!-- MLDSA65_VENDOR_END -->"

# benches we want to surface in protocol_readiness
WANT = [
    "verify_poc_foundry",
    "preA_compute_w_fromPackedA_ntt_rho0_log",
    "preA_compute_w_fromPackedA_ntt_rho1_log",
]

def _load_jsonl(p: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

def _fmt_int(n: Any) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)

def _fmt_float(x: Any) -> str:
    try:
        # keep stable-ish display; don't over-format
        return str(float(x))
    except Exception:
        return str(x)

def _pick_latest_by_ts(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Return mapping bench_name -> selected row (latest by ts_utc).
    """
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        b = r.get("bench_name")
        if b not in WANT:
            continue
        if r.get("scheme") != "mldsa65":
            continue
        ts = r.get("ts_utc", "")
        prev = out.get(b)
        if prev is None or str(ts) > str(prev.get("ts_utc", "")):
            out[b] = r
    return out

def _ensure_markers(report_text: str) -> str:
    """
    If markers are missing entirely, append an empty marker block to the end.
    If BEGIN exists but END doesn't, that's a hard error.
    """
    has_begin = BEGIN in report_text
    has_end = END in report_text

    if has_begin and not has_end:
        raise SystemExit(f"Found {BEGIN} but missing {END} in report; refusing to patch.")

    if not has_begin and not has_end:
        # Append marker scaffold (so patching becomes idempotent)
        if not report_text.endswith("\n"):
            report_text += "\n"
        report_text += "\n" + BEGIN + "\n" + END + "\n"
        return report_text

    # both present
    return report_text

def _build_block(selected: Dict[str, Dict[str, Any]]) -> str:
    lines: List[str] = []

    lines.append(BEGIN)
    lines.append("## ML-DSA-65 (vendor / pinned ref) — measured points")
    lines.append("")
    lines.append(
        "These rows are produced by `scripts/run_vendor_mldsa.sh` and currently require pinning "
        "`MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA` because upstream `main` does not "
        "contain the gas harness tests (`test_verify_gas_poc`, `PreA_ComputeW_GasMicro`) yet."
    )
    lines.append("")
    lines.append(
        "Note: the dataset currently records ML-DSA-65 rows with `security_metric_type=lambda_eff` "
        "and `value=128`. To avoid rewriting later, the table keeps that denominator, and `notes` "
        "additionally reports `security_equiv_bits=192` and `gas/bit@192` (= gas_verify/192)."
    )
    lines.append("")

    # Try to surface vector pack provenance (so it is searchable in the report).
    vref = vid = vpack = None
    for b in WANT:
        r = selected.get(b)
        if not r:
            continue
        if r.get("vector_pack_ref"):
            vref = r.get("vector_pack_ref")
            vpack = r.get("vector_pack_id")
            vid = r.get("vector_id")
            break

    if vref or vpack or vid:
        lines.append("Vector pack (shared reference for these measurements):")
        if vref:
            lines.append(f"- `vector_pack_ref`: `{vref}`")
        if vpack:
            lines.append(f"- `vector_pack_id`: `{vpack}`")
        if vid:
            lines.append(f"- `vector_id`: `{vid}`")
        lines.append("")

    lines.append("Reproduce:")
    lines.append("")
    lines.append("```bash")
    lines.append("export MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA")
    lines.append("bash scripts/run_vendor_mldsa.sh")
    lines.append("bash scripts/make_reports.sh")
    lines.append("```")
    lines.append("")

    lines.append("| bench | gas_verify | denom | value | gas/bit | vendor commit | notes |")
    lines.append("|---|---:|---|---:|---:|---|---|")

    for bench in WANT:
        r = selected.get(bench)
        if not r:
            lines.append(f"| `{bench}` | _missing_ |  |  |  |  |  |")
            continue

        gas = r.get("gas_verify", "")
        denom = r.get("security_metric_type", "")
        val = r.get("security_metric_value", "")
        gpb = r.get("gas_per_secure_bit", "")
        commit = str(r.get("commit", ""))[:12]
        notes = str(r.get("notes", ""))

        # sec192 normalization hint for ML-DSA-65
        sec192 = 192
        gpb192 = ""
        try:
            gpb192 = f"{(int(gas) / sec192):,.6f}".rstrip("0").rstrip(".")
        except Exception:
            gpb192 = ""

        extra = f"sec192=192 gpb192={gpb192}" if gpb192 else "sec192=192"

        lines.append(
            f"| `{bench}` | {_fmt_int(gas)} | `{denom}` | {_fmt_float(val)} | {_fmt_float(gpb)} | `{commit}` | {extra} | {notes[:90]}{'...' if len(notes)>90 else ''} |"
        )

    lines.append(END)
    return "\n".join(lines) + "\n"

def _patch_between_markers(report_text: str, new_block: str) -> str:
    i = report_text.find(BEGIN)
    j = report_text.find(END)
    if i == -1 or j == -1 or j < i:
        raise SystemExit(f"Markers not found in report. Expected {BEGIN} ... {END}")

    j_end = j + len(END)
    before = report_text[:i].rstrip("\n") + "\n\n"
    after = report_text[j_end:].lstrip("\n")
    return before + new_block + "\n" + after

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default="data/results.jsonl")
    ap.add_argument("--report", default="reports/protocol_readiness.md")
    args = ap.parse_args()

    jsonl_path = Path(args.jsonl)
    report_path = Path(args.report)

    if not jsonl_path.exists():
        raise SystemExit(f"JSONL not found: {jsonl_path}")
    if not report_path.exists():
        raise SystemExit(f"Report not found: {report_path}")

    rows = _load_jsonl(jsonl_path)
    selected = _pick_latest_by_ts(rows)

    report_text = report_path.read_text(encoding="utf-8")
    report_text = _ensure_markers(report_text)

    new_block = _build_block(selected)
    patched = _patch_between_markers(report_text, new_block)

    report_path.write_text(patched, encoding="utf-8")
    print(f"[patch] wrote {report_path}")

if __name__ == "__main__":
    main()
