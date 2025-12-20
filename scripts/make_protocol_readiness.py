#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a grant-friendly protocol readiness table from data/results.jsonl.

This script is adapted to the canonical gas-per-secure-bit JSONL schema:
- scheme, bench_name (canonical ID is "scheme::bench_name")
- ts_utc (timestamp)
- gas_verify or gas_surface (fallback gas)
- security_metric_type + security_metric_value (supports: lambda_eff, security_equiv_bits, H_min, bits)
- depends_on (weakest-link cap graph)

Output:
- reports/protocol_readiness.md

Design goals:
- Conservative: effective_security_bits is capped by weakest dependency.
- Reproducible: keeps only the latest record per canonical ID by ts_utc (fallback to file order).
- Tolerant: skips meta/unknown records instead of failing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
DATA_JSONL = ROOT / "data" / "results.jsonl"
OUT_MD = ROOT / "reports" / "protocol_readiness.md"


# Grant-facing target bits (not used for computations; display only)
DEFAULT_TARGET_BITS_BY_CATEGORY = {
    "ecdsa": 128,
    "mldsa65": 192,
    "falcon1024": 256,
    "randao": 128,       # placeholder until threat model finalization
    "attestation": 128,  # placeholder until threat model finalization
}

# Human-facing blocker hints keyed by dependency prefix
BLOCKER_HINTS = [
    ("ecdsa::l1_envelope_assumption",
     "Capped by L1 ECDSA envelope assumption (PQ not enshrined end-to-end)."),
    ("randao::l1_randao_mix_surface",
     "Measured gas; H_min denominator is a placeholder until threat model is fixed."),
    ("attestation::relay_attestation_surface",
     "Measured gas; H_min denominator is a placeholder until threat model is fixed."),
]


def _as_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    try:
        if isinstance(x, bool):
            return int(x)
        if isinstance(x, (int,)):
            return int(x)
        if isinstance(x, float):
            return int(x)
        # strings like "128.0"
        return int(float(str(x)))
    except Exception:
        return None


@dataclass
class Record:
    rid: str                      # canonical id, e.g. "falcon1024::qa_handleOps_userop_foundry"
    category: str                 # usually equals scheme
    gas: Optional[int]            # gas_verify or gas_surface
    security_equiv_bits: Optional[int]      # numerator/denominator bits depending on metric
    effective_security_bits: Optional[int]  # if explicitly present (rare)
    depends_on: List[str]
    ts: str
    meta: Dict[str, Any]

    @staticmethod
    def canonical_rid(obj: Dict[str, Any]) -> Optional[str]:
        # Prefer explicit identifiers if present
        rid = obj.get("id") or obj.get("name") or obj.get("bench_id") or obj.get("surface")
        if rid:
            return str(rid)

        scheme = obj.get("scheme") or obj.get("category")
        bench_name = obj.get("bench_name")
        if scheme and bench_name:
            return f"{scheme}::{bench_name}"

        # last-resort fallback
        if bench_name:
            return str(bench_name)

        return None

    @staticmethod
    def parse_security_bits(obj: Dict[str, Any]) -> Optional[int]:
        # Preferred explicit field if present
        seb = obj.get("security_equiv_bits")
        if seb is not None:
            b = _as_int(seb)
            if b is not None:
                return b

        # Canonical metric representation
        smt = obj.get("security_metric_type")
        smv = obj.get("security_metric_value")

        # We accept H_min (entropy denominator placeholder), security_equiv_bits, lambda_eff, and generic bits
        if smv is not None and smt in (None, "", "lambda_eff", "security_equiv_bits", "H_min", "bits", "security_bits"):
            return _as_int(smv)

        # If security_metric_type is unknown, still try to parse numeric value conservatively
        if smv is not None and smt:
            return _as_int(smv)

        return None

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> "Record":
        rid = Record.canonical_rid(obj)
        if not rid:
            raise ValueError("Missing canonical rid")

        category = obj.get("scheme") or obj.get("category")
        if not category:
            if "::" in rid:
                category = rid.split("::", 1)[0]
            else:
                category = "unknown"
        category = str(category)

        gas = obj.get("gas")
        if gas is None:
            gas = obj.get("gas_verify")
        if gas is None:
            gas = obj.get("gas_surface")
        gas_i = _as_int(gas)

        seb = Record.parse_security_bits(obj)
        esb = _as_int(obj.get("effective_security_bits"))

        depends_on = obj.get("depends_on") or []
        if isinstance(depends_on, str):
            depends_on = [depends_on]
        depends_on = [str(x) for x in depends_on]

        ts = str(obj.get("ts_utc") or obj.get("timestamp") or obj.get("ts") or obj.get("time") or "")

        return Record(
            rid=str(rid),
            category=category,
            gas=gas_i,
            security_equiv_bits=seb,
            effective_security_bits=esb,
            depends_on=depends_on,
            ts=ts,
            meta=obj,
        )


def load_latest_records(jsonl_path: Path) -> Dict[str, Record]:
    """
    Keep only the latest record per canonical rid using ts_utc (fallback to later line).
    """
    latest: Dict[str, Tuple[str, int, Record]] = {}

    with jsonl_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)

            try:
                r = Record.from_json(obj)
            except Exception:
                # Tolerant: skip meta lines / unrecognized records
                continue

            ts = r.ts
            prev = latest.get(r.rid)
            if prev is None:
                latest[r.rid] = (ts, i, r)
            else:
                prev_ts, prev_i, _ = prev
                if ts and prev_ts and ts > prev_ts:
                    latest[r.rid] = (ts, i, r)
                elif ts and not prev_ts:
                    latest[r.rid] = (ts, i, r)
                elif (ts == prev_ts and i > prev_i) or (not ts and not prev_ts and i > prev_i):
                    latest[r.rid] = (ts, i, r)

    return {rid: rec for rid, (_, __, rec) in latest.items()}


def compute_effective_security_bits(records: Dict[str, Record]) -> Dict[str, int]:
    """
    Weakest-link model: effective(r) = min( own(r), effective(dep1), ...).
    """
    memo: Dict[str, int] = {}
    visiting: Set[str] = set()

    def own_bits(r: Record) -> int:
        if r.effective_security_bits is not None:
            return int(r.effective_security_bits)
        if r.security_equiv_bits is not None:
            return int(r.security_equiv_bits)
        return 0

    def dfs(rid: str) -> int:
        if rid in memo:
            return memo[rid]
        if rid in visiting:
            # Cycle => conservative
            memo[rid] = 0
            return 0
        visiting.add(rid)

        r = records.get(rid)
        if r is None:
            memo[rid] = 0
            visiting.remove(rid)
            return 0

        cap = own_bits(r)
        for dep in r.depends_on:
            cap = min(cap, dfs(dep))
        memo[rid] = cap
        visiting.remove(rid)
        return cap

    for rid in records.keys():
        dfs(rid)
    return memo


def find_cap_reason(r: Record, eff_map: Dict[str, int]) -> Optional[str]:
    """
    If effective bits are lower than the record's own bits, find which dependency causes the cap.
    """
    own = r.security_equiv_bits if r.security_equiv_bits is not None else r.effective_security_bits
    if own is None:
        return None
    eff = eff_map.get(r.rid, 0)
    if eff >= int(own):
        return None
    # find a dep that matches the cap
    for dep in r.depends_on:
        if eff_map.get(dep, 0) == eff:
            return dep
    return "depends_on"


def blocker_text(dep: Optional[str]) -> str:
    if not dep:
        return ""
    for prefix, txt in BLOCKER_HINTS:
        if dep.startswith(prefix):
            return txt
    return f"Capped by dependency: {dep}"


def fmt_int(x: Optional[int]) -> str:
    return "-" if x is None else str(x)


def main() -> None:
    if not DATA_JSONL.exists():
        raise SystemExit(f"Missing {DATA_JSONL}")

    records = load_latest_records(DATA_JSONL)
    eff_map = compute_effective_security_bits(records)

    rows = list(records.items())
    rows.sort(key=lambda t: (t[1].category, t[0]))

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("# Protocol Readiness Table (auto-generated)")
    lines.append("")
    lines.append("Generated from `data/results.jsonl` using a weakest-link dependency cap model (`depends_on`).")
    lines.append("")
    lines.append("Reproduce:")
    lines.append("```bash")
    lines.append("python3 scripts/make_protocol_readiness.py")
    lines.append("```")
    lines.append("")
    lines.append("| Category | Surface | Gas | effective_security_bits | Target (bits) | Capped by | Blocker |")
    lines.append("|---|---|---:|---:|---:|---|---|")

    for _, r in rows:
        eff = eff_map.get(r.rid, 0)
        target = DEFAULT_TARGET_BITS_BY_CATEGORY.get(r.category, 0)
        cap_dep = find_cap_reason(r, eff_map)
        blocker = blocker_text(cap_dep) if cap_dep else ""
        lines.append(
            f"| {r.category} | `{r.rid}` | {fmt_int(r.gas)} | {eff} | {target} | {cap_dep or '-'} | {blocker} |"
        )

    lines.append("")
    lines.append("Notes:")
    lines.append("- `effective_security_bits` is conservative: it never exceeds the weakest dependency in `depends_on`.")
    lines.append("- `H_min` surfaces are currently placeholders until the threat model is finalized (gas is measured).")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
