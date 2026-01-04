#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a grant-friendly protocol readiness table from data/results.jsonl.

Canonical schema expectations (tolerant):
- scheme, bench_name (canonical ID is "scheme::bench_name")
- ts_utc (timestamp)
- gas_verify or gas_surface (fallback gas)
- security_metric_type + security_metric_value (supports: lambda_eff, security_equiv_bits, H_min, bits)
- depends_on (weakest-link cap graph)

Output:
- reports/protocol_readiness.md

Design goals:
- Conservative: effective_security_bits is capped by weakest dependency.
- Reproducible: keep only latest record per canonical ID by ts_utc (fallback to file order).
- Tolerant: skip malformed/meta records instead of failing.

Important correctness note:
- DO NOT use obj["surface"] as record id. In this repo it is a "surface class"
  (e.g. "sig::verify") and would collide across multiple benchmarks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
DATA_JSONL = ROOT / "data" / "results.jsonl"
OUT_MD = ROOT / "reports" / "protocol_readiness.md"


# Grant-facing target bits (display hint only).
# If category is missing here, we fallback to max(own_bits, effective_bits).
DEFAULT_TARGET_BITS_BY_CATEGORY: Dict[str, int] = {
    "ecdsa": 128,
    "mldsa65": 192,
    "mldsa-65": 192,
    "falcon": 256,
    "falcon1024": 256,
    "dilithium": 128,    # default; bump when you pin level
    "randao": 128,       # placeholder until threat model finalization
    "attestation": 128,  # placeholder until threat model finalization
    "das": 128,          # protocol surface bucket; not a PQ scheme
}


# Used to resolve short depends_on tokens like "erc4337_bundler_ecdsa"
# into canonical "scheme::bench_name" rids.
KNOWN_DEP_PREFIXES: List[str] = [
    "ecdsa",
    "mldsa65",
    "mldsa-65",
    "falcon",
    "falcon1024",
    "dilithium",
    "randao",
    "attestation",
    "das",
]


# Human-facing blocker hints keyed by dependency prefix
BLOCKER_HINTS = [
    ("ecdsa::l1_envelope_assumption",
     "Capped by L1 ECDSA envelope assumption (PQ not enshrined end-to-end)."),
    ("randao::l1_randao_mix_surface",
     "Measured gas; H_min denominator is a placeholder until threat model is fixed."),
    ("attestation::relay_attestation_surface",
     "Measured gas; H_min denominator is a placeholder until threat model is fixed."),
    ("ecdsa::erc4337_bundler_ecdsa",
     "Capped by ERC-4337 bundler ECDSA dependency (weakest-link)."),
]


def _as_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    try:
        if isinstance(x, bool):
            return int(x)
        if isinstance(x, int):
            return int(x)
        if isinstance(x, float):
            return int(x)
        return int(float(str(x)))
    except Exception:
        return None


@dataclass
class Record:
    rid: str                      # canonical id, e.g. "falcon::falcon_handleOps_userOp_e2e"
    category: str                 # usually equals scheme
    gas: Optional[int]            # gas_verify or gas_surface
    security_equiv_bits: Optional[int]      # denominator bits depending on metric
    effective_security_bits: Optional[int]  # if explicitly present (rare)
    depends_on: List[str]
    ts: str
    meta: Dict[str, Any]

    @staticmethod
    def canonical_rid(obj: Dict[str, Any]) -> Optional[str]:
        """
        Canonical ID policy:
        1) Prefer scheme::bench_name
        2) Then fallback to explicit ids (id/name/bench_id)
        3) Then fallback to bench_name alone
        IMPORTANT: do NOT use "surface" as id (collides).
        """
        scheme = obj.get("scheme") or obj.get("category")
        bench_name = obj.get("bench_name") or obj.get("bench")
        if scheme and bench_name:
            return f"{scheme}::{bench_name}"

        rid = obj.get("id") or obj.get("name") or obj.get("bench_id")
        if rid:
            return str(rid)

        if bench_name:
            return str(bench_name)

        return None

    @staticmethod
    def parse_security_bits(obj: Dict[str, Any]) -> Optional[int]:
        seb = obj.get("security_equiv_bits")
        if seb is not None:
            b = _as_int(seb)
            if b is not None:
                return b

        smt = obj.get("security_metric_type")
        smv = obj.get("security_metric_value")

        if smv is not None and smt in (None, "", "lambda_eff", "security_equiv_bits", "H_min", "bits", "security_bits"):
            return _as_int(smv)

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
            category = rid.split("::", 1)[0] if "::" in rid else "unknown"
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
            try:
                obj = json.loads(line)
            except Exception:
                continue

            try:
                r = Record.from_json(obj)
            except Exception:
                continue

            ts = r.ts
            prev = latest.get(r.rid)
            if prev is None:
                latest[r.rid] = (ts, i, r)
                continue

            prev_ts, prev_i, _ = prev

            if ts and prev_ts and ts > prev_ts:
                latest[r.rid] = (ts, i, r)
            elif ts and not prev_ts:
                latest[r.rid] = (ts, i, r)
            elif (ts == prev_ts and i > prev_i) or (not ts and not prev_ts and i > prev_i):
                latest[r.rid] = (ts, i, r)

    return {rid: rec for rid, (_, __, rec) in latest.items()}


def resolve_dep_rid(dep: str, records: Dict[str, Record]) -> str:
    """
    Resolve depends_on tokens to canonical rids.

    Supported patterns:
    - exact rid: "ecdsa::erc4337_bundler_ecdsa"
    - short token: "erc4337_bundler_ecdsa" -> try "*::erc4337_bundler_ecdsa"
      and try known prefixes "ecdsa::" etc.
    """
    dep = dep.strip()
    if not dep:
        return dep

    if dep in records:
        return dep

    # If already scheme::name but not found, keep as-is
    if "::" in dep:
        return dep

    # 1) suffix match: any rid endswith ::dep
    suffix = f"::{dep}"
    suffix_hits = [rid for rid in records.keys() if rid.endswith(suffix)]
    if len(suffix_hits) == 1:
        return suffix_hits[0]

    # 2) known prefix tries
    pref_hits = [f"{p}::{dep}" for p in KNOWN_DEP_PREFIXES if f"{p}::{dep}" in records]
    if len(pref_hits) == 1:
        return pref_hits[0]

    # If ambiguous, keep original token (conservative; cap logic may still work if caller handles 0)
    return dep


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
            dep_rid = resolve_dep_rid(dep, records)
            cap = min(cap, dfs(dep_rid))
        memo[rid] = cap
        visiting.remove(rid)
        return cap

    for rid in records.keys():
        dfs(rid)
    return memo


def find_cap_reason(r: Record, eff_map: Dict[str, int], records: Dict[str, Record]) -> Optional[str]:
    """
    If effective bits are lower than the record's own bits, find which dependency causes the cap.
    """
    own = r.effective_security_bits if r.effective_security_bits is not None else r.security_equiv_bits
    if own is None:
        return None

    eff = eff_map.get(r.rid, 0)
    if eff >= int(own):
        return None

    for dep in r.depends_on:
        dep_rid = resolve_dep_rid(dep, records)
        if eff_map.get(dep_rid, 0) == eff:
            return dep_rid

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

        own = r.effective_security_bits if r.effective_security_bits is not None else r.security_equiv_bits
        own_i = int(own) if own is not None else 0

        target = DEFAULT_TARGET_BITS_BY_CATEGORY.get(r.category, 0)
        if not target:
            target = max(own_i, int(eff))

        cap_dep = find_cap_reason(r, eff_map, records)
        blocker = blocker_text(cap_dep) if cap_dep else ""

        lines.append(
            f"| {r.category} | `{r.rid}` | {fmt_int(r.gas)} | {eff} | {target} | {cap_dep or '-'} | {blocker} |"
        )

    lines.append("")
    lines.append("Notes:")
    lines.append("- `effective_security_bits` is conservative: it never exceeds the weakest dependency in `depends_on`.")
    lines.append("- `H_min` surfaces are currently placeholders until the threat model is finalized (gas is measured).")
    lines.append("- `Target (bits)` is display-only: if a category is unknown, target falls back to `max(own_bits, effective_bits)`.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

