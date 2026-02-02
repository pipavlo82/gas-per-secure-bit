# Key Storage Assumption (annotation axis)

This repo benchmarks **on-chain verification cost** (gas) across different signature schemes and *surfaces* (app / AA / protocol).  
However, *gas-only* comparisons can be misleading if they silently assume different **private key handling models**.

To keep benchmarks comparable without exploding the surface taxonomy, we treat key storage as an **annotation axis**:

- It does **not** change the EVM verifier cost directly.
- It **does** change deployability and the real-world threat model (exfiltration, offline compromise, operational constraints).

This file defines the canonical vocabulary used in dataset rows via `key_storage_assumption`.

---

## Field

### `key_storage_assumption` (string)

Allowed values (v0):

1. `software_exportable`  
2. `tpm_sealed_ephemeral_use`  
3. `tpm_resident_signing`

Optional companion fields:
- `key_storage_notes` (free text)
- `key_storage_ref` (URL / repo+commit pointer to a reference implementation)

---

## Definitions (v0)

### 1) `software_exportable`

**Meaning:** The private key is usable and/or storable in software such that it is *exportable in plaintext at rest* (or equivalently: can be recovered from software memory/storage without requiring a hardware trust boundary).

This includes seed phrases / keyfiles / secrets recoverable under host compromise (e.g., malware or memory scraping).

**Typical examples:**
- Standard software wallets / keyfiles / seeds in app storage
- Keys derived and held entirely in process memory

**Threat model note:** Strongly depends on OS/app isolation. Susceptible to malware, memory scraping, disk compromise, backup leakage, and supply-chain attacks.

---

### 2) `tpm_sealed_ephemeral_use`

**Meaning:** A hardware module (TPM/HSM/TEE) holds a **sealing key** (or wrapping key).  
The wallet's signing key exists **encrypted at rest**, protected by the hardware-sealed key.  
For signing, the signing key is **decrypted ephemerally in process memory**, used, then **explicitly zeroized**.

This is often the best achievable posture when the hardware does **not** natively implement the signing algorithm/curve (e.g., secp256k1 in many TPMs), yet can still protect the key material at rest and reduce offline exfiltration risk.

**Typical properties:**
- Sealing key never leaves hardware
- Key-at-rest is not plaintext-exportable
- Signing uses short-lived plaintext in memory + explicit wiping
- Often PCR-bound (TPM) or enclave-policy-bound (TEE), but details belong in `key_storage_notes`

**Threat model note:** Not equivalent to true hardware-resident signing, but materially stronger than fully software-managed keys for offline theft/exfiltration. Primarily protects against offline theft/exfiltration; it does not prevent key capture under live host compromise during signing.

---

### 3) `tpm_resident_signing`

**Meaning:** The private key is generated/stored/used **entirely within a hardware trust boundary** (e.g., HSM/TEE/TPM). This assumes the hardware can perform the required signing operation natively.  
Signing happens within the hardware boundary; plaintext private key material is never exposed to host process memory.

**Typical examples:**
- HSM-backed signing where the device supports the required algorithm
- Secure Enclave / TPM-backed signing APIs (where supported)

**Threat model note:** Strongest practical posture for key exfiltration resistance, subject to vendor/device policy and API constraints.

---

## Guidance for benchmark rows

- Always set `key_storage_assumption` explicitly for benchmarks intended for cross-project/cross-scheme comparison.
- If unclear, default to **the weakest plausible assumption** (`software_exportable`) and explain in `key_storage_notes`.
- Use `key_storage_ref` to point to an OSS reference implementation where possible (repo + commit/tag).
- Keep the axis **descriptive**, not prescriptive: the benchmark should say what it assumes, not what everyone "must" do.

---

## Examples

### Example A (typical software wallet)

```json
{
  "bench_name": "ecdsa_ecrecover_surface",
  "surface": "sig::erc7913",
  "key_storage_assumption": "software_exportable",
  "key_storage_notes": "Standard software key management (exportable secret)."
}
```

**Note:** `surface` tags are illustrative; align with canonical surface taxonomy in `spec/case_catalog.md`.

### Example B (TPM-sealed at rest, ephemeral decrypt for signing)

```json
{
  "bench_name": "aa_validateUserOp_pq_verify",
  "surface": "aa::validateUserOp",
  "key_storage_assumption": "tpm_sealed_ephemeral_use",
  "key_storage_notes": "TPM-sealed wrapping key; signing key encrypted at rest; ephemeral in-process decrypt + explicit zeroization.",
  "key_storage_ref": "https://example.org/repo@<commit>"
}
```

### Example C (true hardware-resident signing)

```json
{
  "bench_name": "aa_validateUserOp_hybrid_verify",
  "surface": "aa::validateUserOp",
  "key_storage_assumption": "tpm_resident_signing",
  "key_storage_notes": "Hardware supports signing algorithm natively; host never sees plaintext key material."
}
```

---

## Non-goals (v0)

- We do not attempt to standardize PCR policy, HSM vendor semantics, or enclave attestation formats here.
- We do not claim one model is universally "better"; we only make assumptions explicit so gas comparisons remain honest.
- Future versions may refine notes (TPM vs HSM vs TEE) without adding new required enum values.

---

## Integration with gas-per-secure-bit dataset

This annotation axis is **optional** in `data/results.jsonl`. Records without `key_storage_assumption` are assumed to have `software_exportable` as the implicit default.

When comparing benchmarks across schemes or surfaces, reviewers should check if `key_storage_assumption` differs, as it affects operational security posture even though on-chain gas remains unchanged.
