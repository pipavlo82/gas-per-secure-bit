#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def root_dir() -> Path:
    # scripts/parse_bench.py -> repo root
    return Path(__file__).resolve().parents[1]


def utc_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head(repo_path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            text=True
        ).strip()
    except Exception:
        return "unknown"


def parse_input(arg: str) -> List[Dict[str, Any]]:
    """
    Accept either:
      - a JSON string representing one object
      - a path to a file:
          * JSON: a single object {...} or array [...]
          * JSONL: one JSON object per line
    """
    p = Path(arg)
    if p.exists() and p.is_file():
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            return []

        # First try: parse as normal JSON (object or list)
        try:
            obj = json.loads(text)
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, dict)]
            if isinstance(obj, dict):
                return [obj]
        except Exception:
            pass

        # Fallback: treat as JSONL (one object per line)
        rows: List[Dict[str, Any]] = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    # Not a file => treat as single JSON object string
    return [json.loads(arg)]


def get_any(d: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def provenance_override(raw: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Optional upstream provenance override:
      "provenance": {"repo": "...", "commit": "...", "path": "..."}
    """
    prov = raw.get("provenance")
    if not isinstance(prov, dict):
        return None, None, None

    repo = prov.get("repo")
    commit = prov.get("commit")
    path = prov.get("path")

    if repo is not None and not isinstance(repo, str):
        repo = None
    if commit is not None and not isinstance(commit, str):
        commit = None
    if path is not None and not isinstance(path, str):
        path = None

    repo = repo or None
    commit = commit or None
    path = path or None
    return repo, commit, path


def normalize_row(raw: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    # Backward-compatible top-level provenance
    repo = get_any(raw, ["repo"], defaults["repo"])
    commit = get_any(raw, ["commit"], defaults["commit"])

    # Optional upstream provenance override (preferred when present)
    p_repo, p_commit, p_path = provenance_override(raw)
    if p_repo:
        repo = p_repo
    if p_commit:
        commit = p_commit

    # Required-ish fields
    scheme = get_any(raw, ["scheme"], None)
    if not scheme and isinstance(raw.get("context"), dict):
        scheme = get_any(raw["context"], ["scheme"], None)

    bench_name = get_any(raw, ["bench_name", "bench"], None)
    if not bench_name and isinstance(raw.get("context"), dict):
        bench_name = get_any(raw["context"], ["bench_name", "bench"], None)

    if not scheme or not bench_name:
        raise ValueError("Missing required fields: scheme and bench_name")

    chain_profile = get_any(raw, ["chain_profile", "chain-profile"], "unknown")
    gas_verify = int(get_any(raw, ["gas_verify", "gas"], 0))

    sec_type = get_any(raw, ["security_metric_type", "security-type"], "unknown")
    sec_val = float(get_any(raw, ["security_metric_value", "security-value"], 0.0))

    gas_per_bit: Optional[float] = (gas_verify / sec_val) if sec_val > 0 else None

    hash_profile = get_any(raw, ["hash_profile", "hash"], "unknown")
    notes = get_any(raw, ["notes"], "")

    ts = get_any(raw, ["ts_utc", "ts"], defaults["ts_utc"])

    out: Dict[str, Any] = {
        "ts_utc": ts,
        "repo": repo,
        "commit": commit,
        "scheme": scheme,
        "bench_name": bench_name,
        "chain_profile": chain_profile,
        "gas_verify": gas_verify,
        "security_metric_type": sec_type,
        "security_metric_value": sec_val,
        "gas_per_secure_bit": gas_per_bit,
        "hash_profile": hash_profile,
        "notes": notes,
    }

    # Only attach nested provenance object if the input explicitly provided it
    if p_repo or p_commit or p_path:
        out["provenance"] = {"repo": repo, "commit": commit}
        if p_path:
            out["provenance"]["path"] = p_path

    # vNext passthrough fields
    surface_class = get_any(raw, ["surface_class", "surface"], None)
    if isinstance(surface_class, str) and surface_class:
        out["surface_class"] = surface_class

    security_model = raw.get("security_model")
    if isinstance(security_model, str) and security_model:
        out["security_model"] = security_model

    aggregation_mode = raw.get("aggregation_mode")
    if isinstance(aggregation_mode, str) and aggregation_mode:
        out["aggregation_mode"] = aggregation_mode

    depends_on = raw.get("depends_on")
    if isinstance(depends_on, list) and depends_on:
        out["depends_on"] = [str(x) for x in depends_on]
    elif isinstance(depends_on, str) and depends_on.strip():
        out["depends_on"] = depends_on.strip()

    return out


def ensure_results_files(root: Path) -> Tuple[Path, Path]:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = data_dir / "results.jsonl"
    csv_path = data_dir / "results.csv"
    if not jsonl_path.exists():
        jsonl_path.write_text("", encoding="utf-8")
    if not csv_path.exists():
        csv_path.write_text("", encoding="utf-8")
    return jsonl_path, csv_path


def _csv_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _normalize_provenance_for_csv(prov: Any) -> str:
    """
    CSV cell must contain valid JSON object string, not Python dict repr.

    Accept:
      - dict -> compact JSON
      - JSON string -> normalize to compact JSON (if dict)
      - legacy "{'repo': ...}" -> ast.literal_eval -> compact JSON
      - other non-empty string -> keep as-is (do not break)
    """
    if isinstance(prov, dict):
        return _csv_json(prov)

    if isinstance(prov, str) and prov.strip():
        s = prov.strip()

        # already JSON?
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return _csv_json(obj)
            return s
        except Exception:
            pass

        # legacy python dict repr?
        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, dict):
                return _csv_json(obj)
            return s
        except Exception:
            return s

    return ""


def regen_csv_from_jsonl(jsonl_path: Path, csv_path: Path) -> Tuple[int, int]:
    rows: List[Dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    # Current repo schema: 16 cols
    fields = [
        "ts_utc",
        "repo",
        "commit",
        "scheme",
        "bench_name",
        "chain_profile",
        "gas_verify",
        "security_metric_type",
        "security_metric_value",
        "gas_per_secure_bit",
        "hash_profile",
        "security_model",
        "surface_class",
        "notes",
        "depends_on",
        "provenance",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            row_out = {k: r.get(k, "") for k in fields}

            dep = r.get("depends_on")
            if isinstance(dep, list):
                row_out["depends_on"] = _csv_json(dep)
            elif isinstance(dep, str) and dep.strip():
                row_out["depends_on"] = dep
            else:
                row_out["depends_on"] = ""

            row_out["provenance"] = _normalize_provenance_for_csv(r.get("provenance"))

            w.writerow(row_out)

    return len(fields), len(rows)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  parse_bench.py <json_string_or_file_path>     # append to JSONL + rebuild CSV", file=sys.stderr)
        print("  parse_bench.py --regen <jsonl_path>           # rebuild CSV from JSONL only", file=sys.stderr)
        return 1

    root = root_dir()
    jsonl_path, csv_path = ensure_results_files(root)

    # Regen-only mode (used to keep CSV clean)
    if sys.argv[1] == "--regen":
        src = Path(sys.argv[2]) if len(sys.argv) >= 3 else jsonl_path
        cols, nrows = regen_csv_from_jsonl(src, csv_path)
        print(f"WROTE {csv_path} cols={cols} rows={nrows}")
        return 0

    defaults = {
        "repo": root.name,
        "commit": git_head(root),
        "ts_utc": utc_ts(),
    }

    try:
        raw_rows = parse_input(sys.argv[1])
        normalized: List[Dict[str, Any]] = []
        for r in raw_rows:
            normalized.append(normalize_row(r, defaults))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    # Append JSONL
    with jsonl_path.open("a", encoding="utf-8") as f:
        for r in normalized:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Full regen CSV from JSONL (ensures provenance is JSON, not repr)
    cols, nrows = regen_csv_from_jsonl(jsonl_path, csv_path)
    print(f"WROTE {csv_path} cols={cols} rows={nrows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
