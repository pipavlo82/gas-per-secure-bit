#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Iterator

# Canonical chain_profile normalization (dataset-wide)
CHAIN_PROFILE_ALIASES = {
    # L1
    "evm-l1": "EVM/L1",
    "evm/l1": "EVM/L1",
    "evm_l1": "EVM/L1",
    "l1": "EVM/L1",
    "evm mainnet": "EVM/L1",
    "evm-mainnet": "EVM/L1",
    # L2
    "evm-l2": "EVM/L2",
    "evm/l2": "EVM/L2",
    "evm_l2": "EVM/L2",
    "l2": "EVM/L2",
}

CSV_FIELDS = [
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
    "surface_id",
    "method",
    "surface_layer",
    "hash_profile",
    "security_model",
    "surface_class",
    "key_storage_assumption",
    "notes",
    "depends_on",
    "provenance",
    "vector_pack_ref",
    "vector_pack_id",
    "vector_id",
]


def normalize_chain_profile(v: Any) -> str:
    if v is None:
        return "unknown"
    s = str(v).strip()
    if not s:
        return "unknown"
    return CHAIN_PROFILE_ALIASES.get(s.lower(), s)


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


def parse_input(arg: str) -> Iterator[Dict[str, Any]]:
    """
    Accept either:
      - a JSON string representing one object
      - a path to a file:
          * JSON: a single object {...} or array [...]
          * JSONL: one JSON object per line
    """
    p = Path(arg)
    if p.exists() and p.is_file():
        # Try to parse as a standard JSON file (object or list) first
        try:
            with p.open("r", encoding="utf-8") as f:
                # json.load reads from the file stream directly
                obj = json.load(f)
                if isinstance(obj, list):
                    for x in obj:
                        if isinstance(x, dict):
                            yield x
                    return
                if isinstance(obj, dict):
                    yield obj
                    return
        except Exception:
            # Not a valid single JSON document, fall back to JSONL
            pass

        # Fallback: treat as JSONL (one object per line)
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
        return

    # Not a file => treat as single JSON object string
    try:
        obj = json.loads(arg)
        if isinstance(obj, list):
            for x in obj:
                if isinstance(x, dict):
                    yield x
        elif isinstance(obj, dict):
            yield obj
    except Exception:
        pass


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


def _ensure_canonical_and_legacy_keys(out: Dict[str, Any]) -> None:
    """
    Canonical (new) keys:
      - gas
      - denominator
      - denom_bits
      - gas_per_bit

    Legacy keys (CSV/reports compatibility):
      - gas_verify
      - security_metric_type
      - security_metric_value
      - gas_per_secure_bit

    Policy:
      - If canonical is missing but legacy exists: derive canonical.
      - If legacy is missing but canonical exists: derive legacy.
      - Keep existing values if present (do not override).
    """
    # -------- derive canonical from legacy (if needed)
    if "gas" not in out and "gas_verify" in out and out["gas_verify"] is not None:
        out["gas"] = out["gas_verify"]

    if "denominator" not in out and "security_metric_type" in out and out["security_metric_type"] is not None:
        out["denominator"] = out["security_metric_type"]

    if "denom_bits" not in out and "security_metric_value" in out and out["security_metric_value"] is not None:
        out["denom_bits"] = out["security_metric_value"]

    if "gas_per_bit" not in out:
        g = out.get("gas")
        b = out.get("denom_bits")
        if isinstance(g, (int, float)) and isinstance(b, (int, float)) and b > 0:
            out["gas_per_bit"] = float(g) / float(b)

    # -------- derive legacy from canonical (if needed)
    if "gas_verify" not in out and "gas" in out:
        out["gas_verify"] = out["gas"]

    if "security_metric_type" not in out and "denominator" in out:
        out["security_metric_type"] = out["denominator"]

    if "security_metric_value" not in out and "denom_bits" in out:
        out["security_metric_value"] = out["denom_bits"]

    if "gas_per_secure_bit" not in out and "gas_per_bit" in out:
        out["gas_per_secure_bit"] = out["gas_per_bit"]


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

    chain_profile = normalize_chain_profile(get_any(raw, ["chain_profile", "chain-profile"], "unknown"))

    # Canonical gas/security (preferred)
    gas = get_any(raw, ["gas"], None)
    if gas is None:
        gas = get_any(raw, ["gas_verify"], 0)
    gas = int(gas)

    denominator = get_any(raw, ["denominator"], None)
    if denominator is None:
        denominator = get_any(raw, ["security_metric_type", "security-type"], "unknown")

    denom_bits = get_any(raw, ["denom_bits"], None)
    if denom_bits is None:
        denom_bits = get_any(raw, ["security_metric_value", "security-value"], 0.0)
    denom_bits = float(denom_bits)

    gas_per_bit: Optional[float] = (gas / denom_bits) if denom_bits > 0 else None

    # Keep legacy names too (source compatibility)
    gas_verify = int(get_any(raw, ["gas_verify"], gas))
    sec_type = get_any(raw, ["security_metric_type", "security-type"], denominator)
    sec_val = float(get_any(raw, ["security_metric_value", "security-value"], denom_bits))
    gas_per_secure_bit = gas_per_bit

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

        # Canonical
        "gas": gas,
        "denominator": denominator,
        "denom_bits": denom_bits,
        "gas_per_bit": gas_per_bit,

        # Legacy (for CSV/reports)
        "gas_verify": gas_verify,
        "security_metric_type": sec_type,
        "security_metric_value": sec_val,
        "gas_per_secure_bit": gas_per_secure_bit,

        "hash_profile": hash_profile,
        "notes": notes,
    }

    # Only attach nested provenance object if the input explicitly provided it
    if p_repo or p_commit or p_path:
        out["provenance"] = {"repo": repo, "commit": commit}
        if p_path:
            out["provenance"]["path"] = p_path

    # vNext passthrough fields
    surface_id = raw.get("surface_id")
    if isinstance(surface_id, str) and surface_id:
        out["surface_id"] = surface_id

    method = raw.get("method")
    if isinstance(method, str) and method:
        out["method"] = method

    surface_layer = raw.get("surface_layer")
    if isinstance(surface_layer, str) and surface_layer:
        out["surface_layer"] = surface_layer

    lane_assumption = raw.get("lane_assumption")
    if isinstance(lane_assumption, str) and lane_assumption:
        out["lane_assumption"] = lane_assumption

    wiring_lane = raw.get("wiring_lane")
    if isinstance(wiring_lane, str) and wiring_lane:
        out["wiring_lane"] = wiring_lane

    surface_class = get_any(raw, ["surface_class", "surface"], None)
    if isinstance(surface_class, str) and surface_class:
        out["surface_class"] = surface_class

    security_model = raw.get("security_model")
    if isinstance(security_model, str) and security_model:
        out["security_model"] = security_model

    aggregation_mode = raw.get("aggregation_mode")
    if isinstance(aggregation_mode, str) and aggregation_mode:
        out["aggregation_mode"] = aggregation_mode

    key_storage_assumption = raw.get("key_storage_assumption")
    if isinstance(key_storage_assumption, str) and key_storage_assumption:
        out["key_storage_assumption"] = key_storage_assumption

    vector_pack_ref = raw.get("vector_pack_ref")
    if isinstance(vector_pack_ref, str) and vector_pack_ref:
        out["vector_pack_ref"] = vector_pack_ref

    vector_pack_id = raw.get("vector_pack_id")
    if isinstance(vector_pack_id, str) and vector_pack_id:
        out["vector_pack_id"] = vector_pack_id

    vector_id = raw.get("vector_id")
    if isinstance(vector_id, str) and vector_id:
        out["vector_id"] = vector_id

    depends_on = raw.get("depends_on")
    if isinstance(depends_on, list) and depends_on:
        out["depends_on"] = [str(x) for x in depends_on]
    elif isinstance(depends_on, str) and depends_on.strip():
        out["depends_on"] = depends_on.strip()

    # Ensure both canonical and legacy keys exist (even if upstream sent mixed)
    _ensure_canonical_and_legacy_keys(out)

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


def prepare_csv_row(r: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure legacy keys exist even if JSONL row only had canonical keys
    _ensure_canonical_and_legacy_keys(r)

    row_out = {k: r.get(k, "") for k in CSV_FIELDS}

    dep = r.get("depends_on")
    if isinstance(dep, list):
        row_out["depends_on"] = _csv_json(dep)
    elif isinstance(dep, str) and dep.strip():
        row_out["depends_on"] = dep
    else:
        row_out["depends_on"] = ""

    row_out["provenance"] = _normalize_provenance_for_csv(r.get("provenance"))

    if "key_storage_assumption" not in r or not str(r.get("key_storage_assumption") or "").strip():
        row_out["key_storage_assumption"] = "unknown"

    return row_out


def regen_csv_from_jsonl(jsonl_path: Path, csv_path: Path) -> Tuple[int, int]:
    count = 0
    with csv_path.open("w", newline="", encoding="utf-8") as f_out:
        w = csv.DictWriter(f_out, fieldnames=CSV_FIELDS)
        w.writeheader()

        with jsonl_path.open("r", encoding="utf-8") as f_in:
            for i, line in enumerate(f_in, 1):
                s = line.strip()
                if not s:
                    continue
                try:
                    r = json.loads(s)
                    row_out = prepare_csv_row(r)
                    w.writerow(row_out)
                    count += 1
                except Exception as e:
                    raise SystemExit(f"BAD JSON in {jsonl_path} on line {i}: {e}") from e

    return len(CSV_FIELDS), count


def append_to_csv(rows: List[Dict[str, Any]], csv_path: Path) -> None:
    # Check if header exists
    needs_header = False
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        needs_header = True

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if needs_header:
            w.writeheader()
        for r in rows:
            w.writerow(prepare_csv_row(r))


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  parse_bench.py <json_string_or_file_path>     # append to JSONL + append to CSV", file=sys.stderr)
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

    normalized: List[Dict[str, Any]] = []
    try:
        # parse_input is a generator
        for r in parse_input(sys.argv[1]):
            normalized.append(normalize_row(r, defaults))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not normalized:
        print("WARN: No valid rows found in input", file=sys.stderr)
        return 0

    # Append JSONL
    with jsonl_path.open("a", encoding="utf-8") as f:
        for r in normalized:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Append to CSV (optimization: avoid full regen)
    append_to_csv(normalized, csv_path)

    print(f"APPENDED {len(normalized)} rows to {jsonl_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
