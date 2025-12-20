#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def record_id(r: Dict[str, Any]) -> str:
    # Stable enough: scheme + bench_name
    return f"{r.get('scheme','unknown')}::{r.get('bench_name','unknown')}"


def _as_float(x: Any) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def pick_security_bits(r: Dict[str, Any]) -> Optional[float]:
    """
    Return a bit-like denominator for weakest-link min().

    Accepts:
      - security_metric_type == "security_equiv_bits"  (signatures normalization)
      - security_metric_type == "lambda_eff"           (treated as bits)
      - security_metric_type == "H_min"                (min-entropy bits for entropy/attestation surfaces)
    """
    t = r.get("security_metric_type")
    v = _as_float(r.get("security_metric_value"))
    if v is None:
        return None
    if t in ("security_equiv_bits", "lambda_eff", "H_min"):
        return v
    return None


@dataclass
class WLRow:
    rid: str
    chain_profile: str
    declared_bits: Optional[float]
    depends_on: List[str]
    effective_bits: Optional[float]


def main() -> int:
    root = root_dir()
    jsonl_path = root / "data" / "results.jsonl"
    rows = load_jsonl(jsonl_path)

    # Index by record_id and also by bench_name
    by_id: Dict[str, Dict[str, Any]] = {record_id(r): r for r in rows}

    by_bench: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        bn = str(r.get("bench_name", ""))
        if bn:
            by_bench.setdefault(bn, []).append(r)

    # Weakest-link candidates:
    #  - explicit security_model=weakest_link
    #  - or any record with non-empty depends_on
    wl_candidates: List[Dict[str, Any]] = []
    for r in rows:
        sm = r.get("security_model")
        deps = r.get("depends_on")
        if sm == "weakest_link" or (isinstance(deps, list) and len(deps) > 0):
            wl_candidates.append(r)

    out_dir = root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "weakest_link_report.md"

    lines: List[str] = []
    lines.append("# Weakest-link analysis (AA / protocol envelope dominance)")
    lines.append("")
    lines.append("This report is generated from `data/results.jsonl`.")
    lines.append("")
    lines.append("## Model")
    lines.append("")
    lines.append("- For a pipeline record with dependencies (`depends_on`), define:")
    lines.append("  - `effective_security_bits = min(security_bits(dep_i))` over all dependencies.")
    lines.append("- `security_bits(x)` is taken from records with `security_metric_type` in `{security_equiv_bits, lambda_eff, H_min}`.")
    lines.append("")

    if not wl_candidates:
        lines.append("## Findings")
        lines.append("")
        lines.append("No records with `security_model=weakest_link` or non-empty `depends_on` were found.")
        lines.append("Add `depends_on` to AA/UserOp benchmarks to compute end-to-end effective security.")
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {out_path}")
        return 0

    wl_rows: List[WLRow] = []

    for r in wl_candidates:
        rid = record_id(r)
        chain_profile = str(r.get("chain_profile", "unknown"))
        declared_bits = pick_security_bits(r)

        deps_raw = r.get("depends_on", [])
        depends_on: List[str] = []
        if isinstance(deps_raw, list):
            depends_on = [str(x) for x in deps_raw if isinstance(x, (str, int, float))]

        dep_bits: List[float] = []
        for d in depends_on:
            dep_rec: Optional[Dict[str, Any]] = None

            # 1) Prefer exact scheme::bench_name id
            dep_rec = by_id.get(d)

            # 2) If user passed just "bench_name", accept only if unique
            if dep_rec is None and d in by_bench and len(by_bench[d]) == 1:
                dep_rec = by_bench[d][0]

            # 3) If still none, skip
            if dep_rec is None:
                continue

            b = pick_security_bits(dep_rec)
            if b is not None:
                dep_bits.append(b)

        effective_bits = min(dep_bits) if dep_bits else None
        wl_rows.append(WLRow(rid, chain_profile, declared_bits, depends_on, effective_bits))

    # Write report
    lines.append("## Findings")
    lines.append("")
    lines.append("| Record | Chain | Declared bits | Depends on | Effective bits |")
    lines.append("|---|---|---:|---|---:|")

    for w in wl_rows:
        deps = ", ".join(w.depends_on) if w.depends_on else ""
        db = f"{w.declared_bits:.1f}" if w.declared_bits is not None else ""
        eb = f"{w.effective_bits:.1f}" if w.effective_bits is not None else ""
        lines.append(f"| `{w.rid}` | {w.chain_profile} | {db} | {deps} | {eb} |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Add explicit `depends_on` edges to reflect real execution paths (e.g., AA user op → L1 envelope).")
    lines.append("- Keep baseline envelope assumptions as separate records (e.g., `ecdsa::l1_envelope_assumption`).")
    lines.append("- Entropy/attestation surfaces should use `security_metric_type=H_min` with an explicit threat model in `notes`.")
    lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
