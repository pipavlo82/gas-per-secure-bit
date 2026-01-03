#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys


def die(msg: str, tail: str = "") -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    if tail:
        print("---- forge output tail (last 80 lines) ----", file=sys.stderr)
        print(tail, file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: extract_foundry_gas.py <needle>", file=sys.stderr)
        return 2

    needle = sys.argv[1]
    text = sys.stdin.read()

    # 1) Prefer explicit "(gas: N)" on a line that contains the needle.
    # Example: "[PASS] test_verify_gas_poc() (gas: 68901612)"
    for line in text.splitlines():
        if needle in line and "(gas:" in line:
            m = re.search(r"\(gas:\s*([0-9]+)\)", line)
            if m:
                print(m.group(1))
                return 0

    # 2) Prefer log-style: "<needle> ... gas: N" or "<needle>: N" or "<needle> = N"
    # Example: "gas_compute_w_fromPacked_A_ntt(rho0) gas: 1499354"
    # Example: "gas_compute_w_fromPacked_A_ntt(rho0): 1499354"
    # Example: "gas_compute_w_fromPacked_A_ntt(rho0)=1499354"
    rx = re.compile(
        re.escape(needle) + r".{0,80}?(?:gas\s*[:=]\s*|[:=]\s*)([0-9]+)",
        re.IGNORECASE | re.DOTALL,
    )
    m = rx.search(text)
    if m:
        print(m.group(1))
        return 0

    # 3) Fallback: if there's exactly ONE "(gas: N)" in the entire output, return it.
    # This makes "--match-path <single-test-file>" robust.
    all_gas = re.findall(r"\(gas:\s*([0-9]+)\)", text)
    uniq = sorted(set(all_gas))
    if len(uniq) == 1:
        print(uniq[0])
        return 0

    tail = "\n".join(text.splitlines()[-80:])
    die("could not extract gas from forge output", tail)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
