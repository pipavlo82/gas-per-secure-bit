#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

BEGIN = "<!-- FALCON_VENDOR_BEGIN -->"
END   = "<!-- FALCON_VENDOR_END -->"

# Prefer inserting Falcon block before Dilithium block if Falcon markers absent.
ANCHOR_AFTER = "<!-- MLDSA65_VENDOR_END -->"
ANCHOR_BEFORE = "<!-- DILITHIUM_VENDOR_BEGIN -->"

RESULTS = Path("data/results.jsonl")
OUT_MD  = Path("reports/protocol_readiness.md")

ORDER = [
    "falcon_verifySignature_log",
    "qa_validateUserOp_userop_log",
    "falcon_getUserOpHash_via_entry",
    "falcon_handleOps_userOp_e2e",
]

def _fmt_int(n: Any) -> str:
    try:
        return f"{int(float(n)):,}"
    except Exception:
        return str(n)

def _fmt_float(x: Any) -> str:
    try:
        v = float(x)
        s = f"{v:.10f}".rstrip("0").rstrip(".")
        return s
    except Exception:
        return str(x)

def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            rows.append(json.loads(s))
        except Exception:
            continue
    return rows

def _parse_ts(ts: Optional[str]) -> datetime:
    if not ts:
        return datetime.min
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.min

def _pick_latest(rows: list[Dict[str, Any]], bench_name: str) -> Optional[Dict[str, Any]]:
    cand = [r for r in rows if r.get("bench_name") == bench_name]
    if not cand:
        return None
    cand.sort(key=lambda r: _parse_ts(r.get("ts_utc")), reverse=True)
    return cand[0]

def _build_block(picked: dict[str, Dict[str, Any]]) -> str:
    repo = "QuantumAccount"
    commit_full = ""
    for bn in ORDER:
        if bn in picked:
            commit_full = str(picked[bn].get("commit") or "")
            break
    commit_short = commit_full[:11] if commit_full else ""
    repo_at = f"`{repo}`@`{commit_short}`" if commit_short else f"`{repo}`"

    def note_for(bn: str) -> str:
        if bn == "falcon_verifySignature_log":
            return "log-isolated; Foundry logs: test_falcon_verify_gas_log => 'gas_falcon_verify: <N>'"
        if bn == "qa_validateUserOp_userop_log":
            return "log-isolated; Foundry logs: test_validateUserOp_gas_log => 'gas_validateUserOp: <N>'"
        if bn == "falcon_getUserOpHash_via_entry":
            return "AA surface: EntryPoint hashing only (not end-to-end AA execution)"
        if bn == "falcon_handleOps_userOp_e2e":
            return "end-to-end AA (`handleOps`); treat as protocol-surface upper bound"
        return ""

    lines: list[str] = []
    lines.append(BEGIN)
    lines.append("### Falcon vendor (QuantumAccount) — pinned ref")
    lines.append("")
    lines.append("| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |")
    lines.append("|---|---:|---|---:|---:|---|---|---|")

    for bn in ORDER:
        r = picked.get(bn)
        if not r:
            continue
        gas = _fmt_int(r.get("gas_verify"))
        denom = str(r.get("security_metric_type") or "")
        bits = _fmt_int(r.get("security_metric_value"))
        gpb = _fmt_float(r.get("gas_per_secure_bit"))
        sec_model = str(r.get("security_model") or "")
        n = note_for(bn)
        lines.append(f"| `{bn}` | {gas} | `{denom}` | {bits} | {gpb} | {repo_at} | `{sec_model}` | {n} |")

    lines.append("")
    lines.append("Notes:")
    lines.append(f"- Vendor is pinned by commit in dataset: {repo_at}.")
    lines.append("- `security_equiv_bits = 256` is used as the Falcon-1024 normalization denominator in this repo.")
    lines.append(END)
    return "\n".join(lines)

def _upsert_block(txt: str, block: str) -> str:
    # If markers exist, replace in-place.
    if BEGIN in txt and END in txt:
        pre, rest = txt.split(BEGIN, 1)
        _, post = rest.split(END, 1)
        return pre + block + post

    # Otherwise insert the block at a stable location.
    if ANCHOR_BEFORE in txt:
        return txt.replace(ANCHOR_BEFORE, block + "\n\n" + ANCHOR_BEFORE, 1)

    if ANCHOR_AFTER in txt:
        return txt.replace(ANCHOR_AFTER, ANCHOR_AFTER + "\n\n" + block, 1)

    # Fallback: append at end.
    suffix = "" if txt.endswith("\n") else "\n"
    return txt + suffix + "\n" + block + "\n"

def main() -> None:
    if not OUT_MD.exists():
        raise SystemExit(f"missing {OUT_MD}")

    all_rows = _read_jsonl(RESULTS)
    qa_rows = [r for r in all_rows if r.get("repo") == "QuantumAccount" and r.get("scheme") == "falcon"]

    picked: Dict[str, Dict[str, Any]] = {}
    for bn in ORDER:
        r = _pick_latest(qa_rows, bn)
        if r:
            picked[bn] = r

    block = _build_block(picked)

    txt = OUT_MD.read_text(encoding="utf-8")
    new_txt = _upsert_block(txt, block)
    OUT_MD.write_text(new_txt, encoding="utf-8")
    print(f"[patch] wrote {OUT_MD}")

if __name__ == "__main__":
    main()
