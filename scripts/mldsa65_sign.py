#!/usr/bin/env python3
import json
import hashlib

# Placeholder signer for generating deterministic test vectors

def fake_sign(msg: bytes):
    h = hashlib.sha256(msg).digest()
    return {
        "message": msg.hex(),
        "signature": "00" * 3309,
        "pubkey": "11" * 1952,
        "hash": h.hex(),
    }

if __name__ == "__main__":
    v = fake_sign(b"test-message")
    with open("test_vectors/vector_001.json", "w") as f:
        json.dump(v, f, indent=2)
    print("Generated test_vectors/vector_001.json")
