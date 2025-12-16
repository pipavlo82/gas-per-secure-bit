#!/usr/bin/env python3
import re, sys

needle = sys.argv[1] if len(sys.argv) > 1 else None
text = sys.stdin.read()

if needle:
    lines = [ln for ln in text.splitlines() if needle in ln]
    if lines:
        text = "\n".join(lines)

patterns = [
    r"\(gas:\s*([0-9]+)\)",          # (gas: 123)
    r":\s*([0-9]+)\s*$",             # "...: 123" at end of line (your PreA logs)
    r"\bgas[:=]\s*([0-9]+)\b",       # gas: 123 / gas=123
]

for pat in patterns:
    m = re.search(pat, text, flags=re.MULTILINE)
    if m:
        print(m.group(1))
        sys.exit(0)

print("ERROR: could not find gas number in forge output", file=sys.stderr)
sys.exit(2)
