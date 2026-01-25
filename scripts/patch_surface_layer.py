#!/usr/bin/env python3
import json
from pathlib import Path

p = Path("data/results.jsonl")
rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

def set_if_missing(r, v):
    if not isinstance(r.get("surface_layer"), str) or not r["surface_layer"].strip():
        r["surface_layer"] = v
        return 1
    return 0

changed = 0
for r in rows:
    sid = (r.get("surface_id") or "").strip()

    # settlement: ZK verifier gas on L1 (e.g. Groth16/BN254)
    if sid.startswith("zk::"):
        changed += set_if_missing(r, "settlement")
        continue

    # protocol: protocol-facing / envelope / L1-native system constraints
    if sid.startswith("sigproto::") or sid.startswith("env::") or sid.startswith("entropy::") or sid.startswith("attestation::") or sid.startswith("da::"):
        changed += set_if_missing(r, "protocol")
        continue

    # execution: app/contract-facing execution surfaces (AA, ERC interfaces, signature verify)
    if sid.startswith("aa::") or sid.startswith("sig::"):
        changed += set_if_missing(r, "execution")
        continue

print("patched rows:", changed)
p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
