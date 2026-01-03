#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

BEGIN = "<!-- MLDSA65_VENDOR_BEGIN -->"
END   = "<!-- MLDSA65_VENDOR_END -->"

TARGET_SCHEME = "mldsa65"
TARGET_REPO_SUBSTR = "ml-dsa-65-ethereum-verification"

# "Real" ML-DSA-65 security-equivalent bits (Cat3) — keep it here so we
# don’t have to rewrite the table later when dataset flips denom types.
SEC_EQ_BITS = 192.0

BENCHES = [
    "verify_poc_foundry",
    "preA_compute_w_fromPackedA_ntt_rho0_log",
    "preA_compute_w_fromPackedA_ntt_rho1_log",
]

def load_jsonl(p: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows

def pick_latest(rows: List[Dict[str, Any]], bench: str) -> Optional[Dict[str, Any]]:
    cand: List[Dict[str, Any]] = []
    for r in rows:
        if r.get("scheme") != TARGET_SCHEME:
            continue
        if r.get("bench_name") != bench:
            continue
        repo = str(r.get("repo", ""))
        if TARGET_REPO_SUBSTR not in repo:
            continue

        # must be a real measurement
        gv = r.get("gas_verify")
        try:
            if int(gv) <= 0:
                continue
        except Exception:
            continue

        cand.append(r)

    if not cand:
        return None

    # Prefer newest ts_utc; ISO strings sort lexicographically if consistent
    cand.sort(key=lambda x: str(x.get("ts_utc", "")))
    return cand[-1]

def fmt_int(n: Any) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)

def fmt_float(x: Any) -> str:
    try:
        return f"{float(x):,.6f}".rstrip("0").rstrip(".")
    except Exception:
        return str(x)

def safe_notes(s: str, max_len: int = 140) -> str:
    s = (s or "").replace("\n", " ").strip()
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s

def render_section(rows: List[Dict[str, Any]]) -> str:
    latest = {b: pick_latest(rows, b) for b in BENCHES}

    lines: List[str] = []
    lines.append("## ML-DSA-65 (vendor / pinned ref) — measured points")
    lines.append("")
    lines.append(
        "These rows are produced by `scripts/run_vendor_mldsa.sh` and currently require pinning "
        "`MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA` because upstream `main` does not "
        "contain the gas harness tests (`test_verify_gas_poc`, `PreA_ComputeW_GasMicro`) yet."
    )
    lines.append("")
    lines.append(
        "Note: the dataset currently records ML-DSA-65 rows with `security_metric_type=lambda_eff` and `value=128`. "
        "To avoid rewriting later, the table keeps that denominator, and `notes` additionally reports "
        f"`security_equiv_bits={int(SEC_EQ_BITS)}` and `gas/bit@{int(SEC_EQ_BITS)}` (= gas_verify/{int(SEC_EQ_BITS)})."
    )
    lines.append("")
    lines.append("Reproduce:")
    lines.append("")
    lines.append("```bash")
    lines.append("export MLDSA_REF=feature/mldsa-ntt-opt-phase12-erc7913-packedA")
    lines.append("bash scripts/run_vendor_mldsa.sh")
    lines.append("bash scripts/make_reports.sh")
    lines.append("```")
    lines.append("")

    # Table (unchanged columns)
    lines.append("| bench | gas_verify | denom | value | gas/bit | vendor commit | notes |")
    lines.append("|---|---:|---|---:|---:|---|---|")

    for b in BENCHES:
        r = latest[b]
        if r is None:
            lines.append(f"| `{b}` | *(missing)* |  |  |  |  |  |")
            continue

        gas_i = int(r.get("gas_verify"))
        gas = fmt_int(gas_i)

        denom_t = str(r.get("security_metric_type", ""))
        denom_v = fmt_float(r.get("security_metric_value"))
        gpb = fmt_float(r.get("gas_per_secure_bit"))

        gpb192 = fmt_float(gas_i / SEC_EQ_BITS)

        prov = r.get("provenance") or {}
        vcommit = str(prov.get("commit") or r.get("commit") or "")
        if len(vcommit) > 12:
            vcommit = vcommit[:12]

        base_notes = safe_notes(str(r.get("notes", "")), max_len=110)
        # Put sec192 + gas/bit@192 early so it survives truncation.
        notes = f"sec192={int(SEC_EQ_BITS)} gpb192={gpb192} | {base_notes}"

        lines.append(
            f"| `{b}` | {gas} | `{denom_t}` | {denom_v} | {gpb} | `{vcommit}` | {notes} |"
        )

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"

def upsert_block(doc: str, block: str) -> str:
    """
    Robustly ensure exactly ONE vendor block exists.

    Cases handled:
      - BEGIN present but END missing  -> replace from BEGIN to EOF
      - multiple BEGIN/END             -> replace from first BEGIN to last END
      - neither present                -> append block at EOF
    """
    block_wrapped = f"{BEGIN}\n{block}{END}\n"

    bcount = doc.count(BEGIN)
    ecount = doc.count(END)

    if bcount == 0 and ecount == 0:
        return doc.rstrip() + "\n\n" + block_wrapped

    if bcount >= 1 and ecount == 0:
        # dangling BEGIN: replace from first BEGIN to end-of-file
        b = doc.find(BEGIN)
        pre = doc[:b].rstrip() + "\n\n"
        return pre + block_wrapped

    if bcount == 0 and ecount >= 1:
        # dangling END (rare): remove all END markers and append clean block
        cleaned = doc.replace(END, "").rstrip()
        return cleaned + "\n\n" + block_wrapped

    # both present (possibly multiple)
    b = doc.find(BEGIN)
    e = doc.rfind(END)
    if e < b:
        # malformed ordering; fall back to append after cleaning all markers
        cleaned = doc.replace(BEGIN, "").replace(END, "").rstrip()
        return cleaned + "\n\n" + block_wrapped

    e_end = e + len(END)
    pre = doc[:b].rstrip() + "\n\n"
    post = doc[e_end:].lstrip()

    out = pre + block_wrapped
    if post:
        out += "\n" + post
    return out

def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: patch_protocol_readiness_mldsa.py <data/results.jsonl> <reports/protocol_readiness.md>",
            file=sys.stderr,
        )
        return 2

    jsonl_path = Path(sys.argv[1]).resolve()
    md_path = Path(sys.argv[2]).resolve()

    rows = load_jsonl(jsonl_path)
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

    section = render_section(rows)
    md2 = upsert_block(md, section)

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md2, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
