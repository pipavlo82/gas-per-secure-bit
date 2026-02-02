#!/usr/bin/env python3
import json
from pathlib import Path

# Exact mapping by (scheme, bench_name) for legacy rows
MAP = {
    ("randao",      "l1_randao_mix_surface"):                   "entropy::randao_mix_surface",
    ("randao",      "mix_for_sample_selection_surface"):        "entropy::randao_mix_for_sample_selection_surface",
    ("attestation", "relay_attestation_surface"):               "attestation::relay_attestation_surface",
    ("das",         "verify_sample_512b_surface"):              "da::verify_sample_512b_surface",
    ("p256",        "ethdilithium_p256verify_log"):             "sig::p256::verify",
    ("sigproto",    "eip7932_precompile_assumption"):           "sigproto::eip7932_precompile_assumption",
    ("falcon1024",  "qa_handleOps_userop_foundry_weakest_link_sigproto"):
                                                              "aa::handleOps::falcon1024::weakest_link_sigproto",

    # Former aa::unknown::falcon
    ("falcon",      "falcon_verifySignature_log"):              "sig::falcon::verify",
    ("falcon",      "qa_validateUserOp_userop_log"):            "aa::validateUserOp::falcon",
}

def main():
    p = Path("data/results.jsonl")
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

    changed = 0
    missing = []

    for r in rows:
        sid = (r.get("surface_id") or "").strip()
        if sid not in ("unknown::unclassified", "aa::unknown::falcon"):
            continue

        key = ((r.get("scheme") or "").strip(), (r.get("bench_name") or "").strip())
        new = MAP.get(key)
        if not new:
            missing.append((key, sid))
            continue

        if r.get("surface_id") != new:
            r["surface_id"] = new
            changed += 1

    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    print("patched rows:", changed)
    if missing:
        print("UNMAPPED (needs taxonomy decision):")
        for k, sid in missing:
            print(" -", sid, k)

if __name__ == "__main__":
    main()
