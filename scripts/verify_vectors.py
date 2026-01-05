#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import hashlib

try:
    # Ethereum keccak256 (not NIST SHA3-256)
    from Crypto.Hash import keccak  # pycryptodome
except Exception as e:
    print("ERROR: missing dependency for keccak256. Install pycryptodome: pip install pycryptodome", file=sys.stderr)
    raise

def keccak256(data: bytes) -> bytes:
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()

def u16be(n: int) -> bytes:
    return n.to_bytes(2, "big")

def u32be(n: int) -> bytes:
    return n.to_bytes(4, "big")

def gen_stream(profile: str, seed_hex: str, domain: str, out_len: int) -> bytes:
    seed = bytes.fromhex(seed_hex)
    d = domain.encode("utf-8")
    prefix = u16be(len(d)) + d + seed

    if profile == "fips_shake128":
        h = hashlib.shake_128()
        h.update(prefix)
        return h.digest(out_len)

    if profile == "fips_shake256":
        h = hashlib.shake_256()
        h.update(prefix)
        return h.digest(out_len)

    if profile == "keccak_ctr_xof128":
        tag = b"KCTR128"
        return keccak_ctr(prefix, out_len, tag)

    if profile == "keccak_ctr_xof256":
        tag = b"KCTR256"
        return keccak_ctr(prefix, out_len, tag)

    raise ValueError(f"unknown profile: {profile}")

def keccak_ctr(prefix: bytes, out_len: int, tag: bytes) -> bytes:
    out = b""
    i = 0
    while len(out) < out_len:
        blk = prefix + u32be(i) + tag
        out += keccak256(blk)
        i += 1
    return out[:out_len]

def verify_file(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    suite = data.get("suite")
    version = data.get("version")
    vectors = data.get("vectors", [])

    if suite != "evm-pq-xof-vectors" or version != 1:
        print(f"[FAIL] {path}: unexpected suite/version ({suite}/{version})", file=sys.stderr)
        return 1

    fails = 0
    for v in vectors:
        vid = v["id"]
        profile = v["xof_profile"]
        seed_hex = v["seed_hex"]
        domain = v["domain_sep"]
        out_len = int(v["out_len"])
        expected_hex = v["expected_hex"].lower()

        got = gen_stream(profile, seed_hex, domain, out_len).hex()
        if got != expected_hex:
            fails += 1
            print(f"[FAIL] {path} :: {vid}\n  expected={expected_hex}\n  got     ={got}", file=sys.stderr)
        else:
            print(f"[OK] {path} :: {vid}")

    return 1 if fails else 0

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: scripts/verify_vectors.py <file1.json> [file2.json ...]", file=sys.stderr)
        return 2

    rc = 0
    for p in argv[1:]:
        rc |= verify_file(Path(p))
    return rc

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
