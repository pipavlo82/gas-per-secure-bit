// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice Polynomial helpers for ML-DSA-65 over Z_q, q = 8380417 (Dilithium modulus).
library MLDSA65_Poly {
    uint256 internal constant N = 256;
    int32 internal constant Q = 8380417; // fits in int32

    /// @notice r = (a + b) mod q, coefficient-wise
    function add(
        int32[256] memory a,
        int32[256] memory b
    ) internal pure returns (int32[256] memory r) {
        int64 q = int64(Q);
        for (uint256 i = 0; i < N; ++i) {
            int64 tmp = int64(a[i]) + int64(b[i]);
            tmp %= q;
            if (tmp < 0) tmp += q;
            r[i] = int32(tmp);
        }
    }

    /// @notice r = (a - b) mod q, coefficient-wise
    function sub(
        int32[256] memory a,
        int32[256] memory b
    ) internal pure returns (int32[256] memory r) {
        int64 q = int64(Q);
        for (uint256 i = 0; i < N; ++i) {
            int64 tmp = int64(a[i]) - int64(b[i]);
            tmp %= q;
            if (tmp < 0) tmp += q;
            r[i] = int32(tmp);
        }
    }

    /// @notice r = a ∘ b (pointwise) mod q, coefficient-wise multiply
    /// @dev This is a simple reference implementation; later we will replace it
    ///      with Montgomery-based multiplication aligned with the NTT core.
    function pointwiseMul(
        int32[256] memory a,
        int32[256] memory b
    ) internal pure returns (int32[256] memory r) {
        int64 q = int64(Q);
        for (uint256 i = 0; i < N; ++i) {
            int64 tmp = (int64(a[i]) * int64(b[i])) % q;
            if (tmp < 0) tmp += q;
            r[i] = int32(tmp);
        }
    }
}

/// @notice Polynomial vector types and helpers for ML-DSA-65.
/// @dev Parameters match Dilithium3 / ML-DSA-65: k = 6, l = 5.
library MLDSA65_PolyVec {
    uint256 internal constant N = 256;
    uint256 internal constant K = 6; // length of t1 (polyvecK)
    uint256 internal constant L = 5; // length of z, h (polyvecL)

    struct PolyVecL {
        int32[256][L] polys;
    }

    struct PolyVecK {
        int32[256][K] polys;
    }

    /// @notice r = (a + b) mod q, component-wise, for L-length vectors.
    function addL(
        PolyVecL memory a,
        PolyVecL memory b
    ) internal pure returns (PolyVecL memory r) {
        for (uint256 i = 0; i < L; ++i) {
            r.polys[i] = MLDSA65_Poly.add(a.polys[i], b.polys[i]);
        }
    }

    /// @notice r = (a - b) mod q, component-wise, for L-length vectors.
    function subL(
        PolyVecL memory a,
        PolyVecL memory b
    ) internal pure returns (PolyVecL memory r) {
        for (uint256 i = 0; i < L; ++i) {
            r.polys[i] = MLDSA65_Poly.sub(a.polys[i], b.polys[i]);
        }
    }

    /// @notice r = (a + b) mod q, component-wise, for K-length vectors.
    function addK(
        PolyVecK memory a,
        PolyVecK memory b
    ) internal pure returns (PolyVecK memory r) {
        for (uint256 i = 0; i < K; ++i) {
            r.polys[i] = MLDSA65_Poly.add(a.polys[i], b.polys[i]);
        }
    }

    /// @notice r = (a - b) mod q, component-wise, for K-length vectors.
    function subK(
        PolyVecK memory a,
        PolyVecK memory b
    ) internal pure returns (PolyVecK memory r) {
        for (uint256 i = 0; i < K; ++i) {
            r.polys[i] = MLDSA65_Poly.sub(a.polys[i], b.polys[i]);
        }
    }

    /// @notice NTT wrapper for PolyVecL.
    /// @dev TODO: wire to the real NTT core (NTT_MLDSA_Real) later.
    function nttL(
        PolyVecL memory v
    ) internal pure returns (PolyVecL memory r) {
        // Identity placeholder for now.
        return v;
    }

    /// @notice inverse NTT wrapper for PolyVecL.
    function inttL(
        PolyVecL memory v
    ) internal pure returns (PolyVecL memory r) {
        // Identity placeholder for now.
        return v;
    }

    /// @notice NTT wrapper for PolyVecK.
    function nttK(
        PolyVecK memory v
    ) internal pure returns (PolyVecK memory r) {
        // Identity placeholder for now.
        return v;
    }

    /// @notice inverse NTT wrapper for PolyVecK.
    function inttK(
        PolyVecK memory v
    ) internal pure returns (PolyVecK memory r) {
        // Identity placeholder for now.
        return v;
    }
}

/// @notice ML-DSA-65 Verifier v2 – skeleton for the real verification pipeline.
/// @dev For now this only fixes ABI and prepares for the polynomial/NTT layer.
contract MLDSA65_Verifier_v2 {
    using MLDSA65_Poly for int32[256];

    struct PublicKey {
        // FIPS-204 encoded ML-DSA-65 public key (1952 bytes)
        bytes raw;
    }

    struct Signature {
        // FIPS-204 encoded ML-DSA-65 signature (3309 bytes)
        bytes raw;
    }

    /// @notice Main verification entrypoint (not implemented yet).
    function verify(
        PublicKey memory pk,
        Signature memory sig,
        bytes32 message_digest
    ) external pure returns (bool) {
        // Parameters are intentionally unused for now – real logic will be added later.
        pk;
        sig;
        message_digest;

        // TODO:
        // 1) Decode pk.raw → t1, rho, ...
        // 2) Decode sig.raw → z, h, c
        // 3) Compute A * z - c * t1 (poly ops + NTT)
        // 4) Decompose and apply hint
        // 5) Hash check

        return false;
    }
}
