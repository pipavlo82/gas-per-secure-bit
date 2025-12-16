#!/usr/bin/env python3
import re
import sys

needle = sys.argv[1] if len(sys.argv) > 1 else None
text = sys.stdin.read()

if needle:
    lines = [ln for ln in text.splitlines() if needle in ln]
    if lines:
        text = "\n".join(lines)

# 1) Foundry style: "(gas: 123)"
m = re.search(r"\(gas:\s*([0-9]+)\)", text)
if m:
    print(m.group(1))
    sys.exit(0)

# 2) Log style: "something: 123"
ms = re.findall(r":\s*([0-9]+)\s*$", text, flags=re.M)
if ms:
    print(ms[-1])
    sys.exit(0)

print("ERROR: could not extract gas from forge output", file=sys.stderr)
sys.exit(2)
