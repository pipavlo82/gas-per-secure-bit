#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Upsert a Dilithium vendor block into reports/protocol_readiness.md.

Called by scripts/make_reports.sh as:
  python3 scripts/patch_protocol_readiness_dilithium.py data/results.jsonl reports/protocol_readiness.md

Policy:
- Select latest (by ts_utc ISO8601 lexicographic) per target bench_name
  from repo == "ZKNoxHQ/ETHDILITHIUM" and scheme == "dilithium".
- Replace content between markers if present; otherwise append at end.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


BEGIN = "<!-- DILITHIUM_VENDOR_BEGIN -->"
END = "<!-- DILITHIUM_VENDOR_END -->"

REPO = "ZKNoxHQ/ETHDILITHIUM"

ORDER = [
    "dilithium_verify_nistkat",
    "ethdilithium_verify_evmfriendly",
]


def _as_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return int(x)
        if isinstance(x, int):
            return int(x)
        if isinstance(x, float):
            return int(x)
        return int(float(str(x)))
    except Exception:
        return None


def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        return float(str(x))
    except Exception:
        return None


def _fmt_int(x: Any) -> str:
    v = _as_int(x)
    return "0" if v is None else f"{v:,}"


def _fmt_bits(x: Any) -> str:
    v = _as_int(x)
    return "0" if v is None else str(v)


def _fmt_float(x: Any) -> str:
    v = _as_float(x)
    return "0" if v is None else str(v)


def _latest_for_bench(jsonl_path: Path, bench_name: str) -> Optional[Dict[str, Any]]:
    best: Optional[Dict[str, Any]] = None
    best_ts = ""

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            if obj.get("repo") != REPO:
                continue
            if obj.get("scheme") != "dilithium":
                continue
            if obj.get("bench_name") != bench_name:
                continue

            ts = str(obj.get("ts_utc") or "")
            if (best is None) or (ts and ts >= best_ts):
                best = obj
                best_ts = ts

    return best


def _build_block(picked: Dict[str, Dict[str, Any]]) -> str:
    commit_full = ""
    for bn in ORDER:
        if bn in picked:
            commit_full = str(picked[bn].get("commit") or "")
            break
    commit_short = commit_full[:11] if commit_full else ""
    repo_at = f"`{REPO}`@`{commit_short}`" if commit_short else f"`{REPO}`@`(none)`"

    def note_for(bn: str) -> str:
        # Keep these short; the raw record notes (sec128=..., etc.) are already useful.
        if bn == "dilithium_verify_nistkat":
            return "path-pinned; Foundry: test/ZKNOX_dilithiumKATS.t.sol:testVerify"
        if bn == "ethdilithium_verify_evmfriendly":
            return "path-pinned; Foundry: test/ZKNOX_ethdilithiumKAT.t.sol:testVerify"
        return ""

    lines: list[str] = []
    lines.append(BEGIN)
    lines.append("### Dilithium vendor (ZKNoxHQ/ETHDILITHIUM) — pinned ref")
    lines.append("")
    lines.append("| bench | gas | security_metric | bits | gas/bit | repo@commit | security_model | notes |")
    lines.append("|---|---:|---|---:|---:|---|---|---|")

    if not picked:
        lines.append(
            "| _(missing)_ | 0 | `security_equiv_bits` | 0 | 0 | "
            f"{repo_at} | `standalone` | run scripts/run_vendor_dilithium_ethdilithium.sh |"
        )
    else:
        for bn in ORDER:
            r = picked.get(bn)
            if not r:
                continue
            gas = _fmt_int(r.get("gas_verify"))
            denom = str(r.get("security_metric_type") or "")
            bits = _fmt_bits(r.get("security_metric_value"))
            gpb = _fmt_float(r.get("gas_per_secure_bit"))
            sec_model = str(r.get("security_model") or r.get("security_model_type") or "standalone")
            n = str(r.get("notes") or "").strip()
            extra = note_for(bn)
            if extra:
                n = (n + "; " + extra) if n else extra
            lines.append(f"| `{bn}` | {gas} | `{denom}` | {bits} | {gpb} | {repo_at} | `{sec_model}` | {n} |")

    lines.append("")
    lines.append("Notes:")
    lines.append(f"- Vendor is pinned by commit in dataset: {repo_at}.")
    lines.append("- `dilithium_verify_nistkat` is the NIST-shape verifier in the vendor repo.")
    lines.append("- `ethdilithium_verify_evmfriendly` is the EVM-friendly variant in the same vendor repo.")
    lines.append("- Recorded points are signature verification only (sig::verify); AA end-to-end surfaces (validateUserOp/handleOps) are not yet measured for this vendor.")
    lines.append("- Denominator here uses `security_equiv_bits` (override SEC_BITS_* in the runner if you confirm a different category).")
    lines.append(END)
    return "\n".join(lines) + "\n"


def _upsert_block(txt: str, block: str) -> str:
    if BEGIN in txt and END in txt:
        pre = txt.split(BEGIN, 1)[0]
        post = txt.split(END, 1)[1]
        return pre + block + post
    return txt.rstrip() + "\n\n" + block


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: patch_protocol_readiness_dilithium.py <data/results.jsonl> <reports/protocol_readiness.md>", file=sys.stderr)
        return 2

    jsonl_path = Path(argv[1])
    md_path = Path(argv[2])

    if not jsonl_path.exists() or not md_path.exists():
        raise SystemExit("missing results.jsonl or protocol_readiness.md; run scripts/make_reports.sh first")

    picked: Dict[str, Dict[str, Any]] = {}
    for bn in ORDER:
        r = _latest_for_bench(jsonl_path, bn)
        if r is not None:
            picked[bn] = r

    block = _build_block(picked)
    md = md_path.read_text(encoding="utf-8")
    md2 = _upsert_block(md, block)
    md_path.write_text(md2, encoding="utf-8")
    print(f"[patch] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
