import json
import base64

INPUT = "test_vectors/mldsa65_real.json"
OUTPUT = "test_vectors/mldsa65_real_hex.json"

def b64_to_hex(b64str):
    raw = base64.b64decode(b64str)
    return "0x" + raw.hex()

with open(INPUT, "r") as f:
    data = json.load(f)

out = {"vectors": []}

for v in data["vectors"]:
    out["vectors"].append({
        "name": v["name"],
        "msg_hash": v["msg_hash"],                  # already hex
        "pubkey_hex": b64_to_hex(v["pubkey.b64"]), # NEW
        "signature_hex": b64_to_hex(v["sig_pq_b64"]),
        "expected": v["expected"]
    })

with open(OUTPUT, "w") as f:
    json.dump(out, f, indent=2)

print("Done! Wrote:", OUTPUT)
