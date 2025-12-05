import json, base64

data = json.load(open("tmp.json"))
sig_b64 = data["sig_pq_b64"]
pk_b64  = data["pq_pubkey_b64"]
msg     = data["msg_hash"].replace("0x","")

sig_hex = base64.b64decode(sig_b64).hex()
pk_hex  = base64.b64decode(pk_b64).hex()

print("PUBKEY HEX:\n", pk_hex)
print("\nSIGNATURE HEX:\n", sig_hex)
print("\nMSG HASH:\n", msg)

# rewrite vector file
vec = {
    "vectors":[
        {
            "name":"real001",
            "msg_hash": msg,
            "pubkey_hex": pk_hex,
            "signature_hex": sig_hex,
            "expected": True
        }
    ]
}

json.dump(vec, open("test_vectors/mldsa65_real_hex.json","w"), indent=2)
