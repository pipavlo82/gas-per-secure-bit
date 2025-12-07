import json, base64

src = "test_vectors/vector_raw.json"
dst = "test_vectors/vector_001.json"

with open(src) as f:
    d = json.load(f)

# Extract fields
pk_b64 = d["pq_pubkey_b64"]
sig_b64 = d["sig_pq_b64"]
msg_hash = d["msg_hash"]

pk_raw = base64.b64decode(pk_b64).hex()
sig_raw = base64.b64decode(sig_b64).hex()

out = {
    "public_key_raw": "0x" + pk_raw,
    "signature_raw": "0x" + sig_raw,
    "msg_hash": msg_hash
}

with open(dst, "w") as f:
    json.dump(out, f, indent=2)

print("Wrote", dst)
