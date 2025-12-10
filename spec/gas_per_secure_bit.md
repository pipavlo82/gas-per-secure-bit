# Gas per secure bit – metric definition

## 1. Intuition

Blockchains pay for computation in `gas`, but protocols care about **cryptographic security** and **entropy**, measured in bits.

We define a simple metric that connects both:

\[
\text{Gas per secure bit} = \frac{\text{gas\_verify}}{H_\text{min}(\text{object})}
\]

where:

- `gas_verify` – gas units spent to verify a signature or VRF proof on-chain.
- \(H_\text{min}\) – min-entropy (in bits) of the object being verified:
  - for signatures – effective security level λ of the scheme,
  - for randomness – min-entropy of the random output under a given threat model.

This allows comparing schemes not just by “gas per verify”, but by **gas cost per unit of cryptographic security**.

---

## 2. Signatures

For a signature scheme with security level λ (e.g. 128-bit):

- We approximate:
  \[
  H_\text{min}(\text{signature}) \approx \lambda_\text{eff}
  \]
  where \(\lambda_\text{eff}\) is the effective security level after known attacks.

- The metric becomes:
  \[
  \text{Gas per secure bit}_\text{sig} =
  \frac{\text{gas\_verify}}{\lambda_\text{eff}}
  \]

Example (ML-DSA-65, 128-bit profile):

- `gas_verify` = 2,700,000 gas (example benchmark),
- \(\lambda_\text{eff} = 128\) bits,

then:
\[
\text{Gas per secure bit} =
\frac{2\,700\,000}{128} \approx 21\,093.75 \text{ gas/bit}
\]

In datasets we will always report this together with:

- signature size (bytes),
- `gas_per_byte`,
- latency and trust model.

---

## 3. Verifiable randomness / VRF

For VRF and entropy sources we consider a random output \(Y\) of length `n` bits.

- Ideal case (perfect randomness):
  \[
  H_\text{min}(Y) \approx n
  \]

- Realistic case:
  \[
  H_\text{min}(Y) = n - \Delta
  \]
  where \(\Delta\) captures bias, manipulation power or grinding ability of an adversary.

The metric:

\[
\text{Gas per secure bit}_\text{vrf} =
\frac{\text{gas\_verify}}{H_\text{min}(Y)}
\]

Here `gas_verify` includes:

- on-chain verification of the VRF proof (or dual signatures),
- optional calldata cost of the proof, if relevant for the protocol.

Examples of sources we want to profile:

- Single-key VRFs (ECDSA, BLS).
- Distributed or committee-based VRFs.
- Beacons and RANDAO-style constructions.
- Sealed-entropy VRFs (e.g. Re4ctoR dual-sig VRF).

---

## 4. Reporting format

For each scheme / chain profile we will publish rows of the form:

```text
scheme,chain,gas_verify,lambda_eff,H_min,gas_per_secure_bit,gas_per_byte,latency_ms,trust_model
MLDSA65,ethereum,2700000,128,128,21093.75,815.9,~,single-verifier
Where:

lambda_eff – effective security level in bits.

H_min – min-entropy used in the denominator (may differ from lambda_eff for randomness).

trust_model – short textual description (single oracle, distributed committee, sequencer, etc.).

5. Scope

This document is intentionally minimal and practical:

It does not try to redefine formal cryptographic security proofs.

It provides a reproducible way to compare on-chain costs for different schemes by a single scalar: gas per secure bit.

Future extensions may add:

latency-adjusted versions (gas × ms per bit),

decentralisation-adjusted versions (gas per decentralised secure bit),

USD-per-secure-bit estimates for economic comparisons.
