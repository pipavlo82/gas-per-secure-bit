// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

//
// =============================
//  Polynomial core (single poly)
// =============================
//

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
    /// @dev Simple reference implementation; later буде замінено на Montgomery/NTT-friendly.
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

//
// =============================
//  PolyVecL / PolyVecK wrappers
// =============================
//

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

    /// @notice NTT wrapper for PolyVecL (placeholder).
    function nttL(
        PolyVecL memory v
    ) internal pure returns (PolyVecL memory r) {
        // Identity placeholder for now.
        return v;
    }

    /// @notice inverse NTT wrapper for PolyVecL (placeholder).
    function inttL(
        PolyVecL memory v
    ) internal pure returns (PolyVecL memory r) {
        // Identity placeholder for now.
        return v;
    }

    /// @notice NTT wrapper for PolyVecK (placeholder).
    function nttK(
        PolyVecK memory v
    ) internal pure returns (PolyVecK memory r) {
        // Identity placeholder for now.
        return v;
    }

    /// @notice inverse NTT wrapper for PolyVecK (placeholder).
    function inttK(
        PolyVecK memory v
    ) internal pure returns (PolyVecK memory r) {
        // Identity placeholder for now.
        return v;
    }
}

//
// ============
//  Hint layer
// ============
//

/// @notice Hint vector helpers for ML-DSA-65.
library MLDSA65_Hint {
    uint256 internal constant N = 256;
    uint256 internal constant L = 5; // hint живе в тому ж L-вимірі

    /// @notice Hint vector: flags in {-1, 0, 1} per coefficient.
    struct HintVecL {
        int8[256][L] flags;
    }

    /// @notice Basic sanity check: all flags must be in {-1, 0, 1}.
    function isValidHint(HintVecL memory h) internal pure returns (bool) {
        for (uint256 j = 0; j < L; ++j) {
            for (uint256 i = 0; i < N; ++i) {
                int8 v = h.flags[j][i];
                if (v < -1 || v > 1) {
                    return false;
                }
            }
        }
        return true;
    }

    /// @notice Placeholder applyHint for PolyVecL.
    /// @dev Поки що це identity; реальна логіка буде додана разом із full decomposition.
    function applyHintL(
        MLDSA65_PolyVec.PolyVecL memory w,
        HintVecL memory /*h*/
    ) internal pure returns (MLDSA65_PolyVec.PolyVecL memory out) {
        return w;
    }
}

//
// ===================
//  Verifier skeleton
// ===================
//

/// @notice ML-DSA-65 Verifier v2 – skeleton для реального verification pipeline.
/// @dev Зараз тут: ABI, decode-шар, підготовка до поліно/NTT шару.
contract MLDSA65_Verifier_v2 {
    using MLDSA65_Poly for int32[256];

    int32 internal constant Q = 8380417;

    // ============================
    // Public key layout constants
    // ============================

    // t1: K=6 polys, N=256, 10 bits per coeff → 6 * 256 * 10 / 8 = 1920 bytes
    uint256 internal constant T1_PACKED_BYTES = 1920;
    uint256 internal constant RHO_BYTES = 32;
    uint256 internal constant PK_MIN_LEN = T1_PACKED_BYTES + RHO_BYTES; // 1952 bytes

    struct PublicKey {
        // FIPS-204 encoded ML-DSA-65 public key (1952 bytes)
        bytes raw;
    }

    struct Signature {
        // FIPS-204 encoded ML-DSA-65 signature (3309 bytes)
        bytes raw;
    }

    struct DecodedPublicKey {
        bytes32 rho;
        MLDSA65_PolyVec.PolyVecK t1;
    }

    struct DecodedSignature {
        bytes32 c;
        MLDSA65_PolyVec.PolyVecL z;
        MLDSA65_Hint.HintVecL h;
    }

    /// @notice Main verification entrypoint (ще не реалізований).
    function verify(
        PublicKey memory pk,
        Signature memory sig,
        bytes32 message_digest
    ) external pure returns (bool) {
        if (pk.raw.length < 32 || sig.raw.length < 32) {
            return false;
        }

        DecodedPublicKey memory dpk = _decodePublicKey(pk);
        DecodedSignature memory dsig = _decodeSignature(sig);

        MLDSA65_PolyVec.PolyVecK memory w = _compute_w(dpk, dsig);
        w;
        message_digest;

        // Поки що завжди false – verification pipeline ще не підключений.
        return false;
    }

    //
    // Decode helpers – оверлоади для сумісності з тестами
    //

    /// @notice Decode public key from struct wrapper.
    function _decodePublicKey(
        PublicKey memory pk
    ) internal pure returns (DecodedPublicKey memory dpk) {
        return _decodePublicKeyRaw(pk.raw);
    }

    /// @notice Decode public key directly from raw bytes (для старих harness-ів).
    function _decodePublicKey(
        bytes memory pkRaw
    ) internal pure returns (DecodedPublicKey memory dpk) {
        return _decodePublicKeyRaw(pkRaw);
    }

    /// @notice Decode signature from struct wrapper.
    function _decodeSignature(
        Signature memory sig
    ) internal pure returns (DecodedSignature memory dsig) {
        return _decodeSignatureRaw(sig.raw);
    }

    /// @notice Decode signature directly from raw bytes (для старих harness-ів).
    function _decodeSignature(
        bytes memory sigRaw
    ) internal pure returns (DecodedSignature memory dsig) {
        return _decodeSignatureRaw(sigRaw);
    }

    //
    // Реальні тіла decode-логіки (Raw)
    //

    /// @notice Decode public key bytes into a structured view.
    /// @dev Два режими:
    ///  - len >= PK_MIN_LEN (1952): повний FIPS-розпак t1 + rho (новий шлях)
    ///  - len < PK_MIN_LEN: legacy-режим (тільки rho + перші 4 coeff t1[0] з offset 32)
    function _decodePublicKeyRaw(
        bytes memory pkRaw
    ) internal pure returns (DecodedPublicKey memory dpk) {
        uint256 len = pkRaw.length;

        // 1) Новий FIPS-режим: повний t1 + rho
        if (len >= PK_MIN_LEN) {
            // rho = останні 32 байти
            uint256 rhoOffset = len - RHO_BYTES;
            bytes32 rhoBytes;
            assembly {
                rhoBytes := mload(add(add(pkRaw, 0x20), rhoOffset))
            }
            dpk.rho = rhoBytes;

            // t1: перші 1920 байтів (упаковані 10-бітні коефіцієнти)
            _decodeT1Packed(pkRaw, dpk.t1);
            return dpk;
        }

        // 2) Legacy-режим (старі тести Decode* очікують таку поведінку).

        // rho = останні 32 байти, якщо їх достатньо
        if (len >= 32) {
            uint256 off = len - 32;
            bytes32 rhoLegacy;
            assembly {
                rhoLegacy := mload(add(add(pkRaw, 0x20), off))
            }
            dpk.rho = rhoLegacy;
        }

        // t1[0][0..3] — старий FIPSPack-режим:
        // перші 4 коефіцієнти беруться з pkRaw[32..36] (5 байтів)
        if (len >= 32 + 5) {
            uint256 base = 32;

            uint16 b0 = uint16(uint8(pkRaw[base]));
            uint16 b1 = uint16(uint8(pkRaw[base + 1]));
            uint16 b2 = uint16(uint8(pkRaw[base + 2]));
            uint16 b3 = uint16(uint8(pkRaw[base + 3]));
            uint16 b4 = uint16(uint8(pkRaw[base + 4]));

            uint16 t0 = uint16((b0 | (b1 << 8)) & 0x03FF);
            uint16 t1c = uint16(((b1 >> 2) | (b2 << 6)) & 0x03FF);
            uint16 t2c = uint16(((b2 >> 4) | (b3 << 4)) & 0x03FF);
            uint16 t3c = uint16(((b3 >> 6) | (b4 << 2)) & 0x03FF);

            dpk.t1.polys[0][0] = int32(int16(t0));
            dpk.t1.polys[0][1] = int32(int16(t1c));
            dpk.t1.polys[0][2] = int32(int16(t2c));
            dpk.t1.polys[0][3] = int32(int16(t3c));
        }

        // якщо len < 32 або < 37 — просто повертаємо те, що є (rho=0, t1=0)
    }

    /// @dev Розпаковує t1 з перших 1920 байтів src у PolyVecK.
    /// Очікуваний формат: для кожного з K поліномів:
    /// 256 коефіцієнтів по 10 біт, запаковані як 64 групи по 4 coeffs → 5 байтів.
    function _decodeT1Packed(
        bytes memory src,
        MLDSA65_PolyVec.PolyVecK memory t1
    ) internal pure {
        require(src.length >= T1_PACKED_BYTES, "t1 too short");

        uint256 byteOffset = 0;

        // K = 6 поліномів
        for (uint256 k = 0; k < MLDSA65_PolyVec.K; ++k) {
            // 64 групи по 4 коефіцієнти на поліном
            for (uint256 group = 0; group < 64; ++group) {
                uint256 idx = byteOffset;

                uint16 b0 = uint16(uint8(src[idx + 0]));
                uint16 b1 = uint16(uint8(src[idx + 1]));
                uint16 b2 = uint16(uint8(src[idx + 2]));
                uint16 b3 = uint16(uint8(src[idx + 3]));
                uint16 b4 = uint16(uint8(src[idx + 4]));

                byteOffset += 5;

                uint256 baseIdx = group * 4;

                uint16 t0 = (           b0         | ((b1 & 0x03) << 8)) & 0x03FF;
                uint16 t1c = ((b1 >> 2)            | ((b2 & 0x0F) << 6)) & 0x03FF;
                uint16 t2 = ((b2 >> 4)            | ((b3 & 0x3F) << 4)) & 0x03FF;
                uint16 t3 = ((b3 >> 6)            |  (b4        << 2))  & 0x03FF;

                t1.polys[k][baseIdx + 0] = int32(uint32(t0));
                t1.polys[k][baseIdx + 1] = int32(uint32(t1c));
                t1.polys[k][baseIdx + 2] = int32(uint32(t2));
                t1.polys[k][baseIdx + 3] = int32(uint32(t3));
            }
        }
    }

    /// @notice Decode signature bytes into a structured view.
    /// @dev Поточна поведінка:
    ///  - c береться з останніх 32 байтів sigRaw
    ///  - перші кілька коефіцієнтів z[0] – з початку sigRaw (LE, 4 байти на coeff)
    function _decodeSignatureRaw(
        bytes memory sigRaw
    ) internal pure returns (DecodedSignature memory dsig) {
        uint256 len = sigRaw.length;

        // c = останні 32 байти
        if (len >= 32) {
            uint256 off = len - 32;
            bytes32 cBytes;
            assembly {
                cBytes := mload(add(add(sigRaw, 0x20), off))
            }
            dsig.c = cBytes;
        }

        // z[0][0..3] = перші 4 coeff з початку sigRaw (LE, 4 байти на coeff)
        uint256 maxCoeffs = 4;
        for (uint256 i = 0; i < maxCoeffs; ++i) {
            uint256 off = i * 4;
            if (off + 4 > len) {
                break;
            }
            int32 coeff = _decodeCoeffLE(sigRaw, off);
            dsig.z.polys[0][i] = coeff;
        }
    }

    //
    // Low-level coeff decode
    //

    /// @notice Decode a single coefficient from 4 bytes in little-endian order, reduced mod Q.
    /// @dev Низькорівневий helper; буде використаний і в реальному FIPS-204 packing.
    function _decodeCoeffLE(
        bytes memory src,
        uint256 offset
    ) internal pure returns (int32) {
        require(offset + 4 <= src.length, "coeff decode out of bounds");

        uint32 v =
            uint32(uint8(src[offset])) |
            (uint32(uint8(src[offset + 1])) << 8) |
            (uint32(uint8(src[offset + 2])) << 16) |
            (uint32(uint8(src[offset + 3])) << 24);

        uint32 q = uint32(uint32(uint256(int256(Q))));
        uint32 reduced = v % q;
        return int32(int256(uint256(reduced)));
    }

    //
    // Structural placeholder for w = A * z - c * t1
    //

    /// @notice Structural placeholder for w = A * z - c * t1 in ML-DSA-65.
    /// @dev Поки що просто повертаємо t1 як w, щоб pipeline був зібраний.
    function _compute_w(
        DecodedPublicKey memory dpk,
        DecodedSignature memory dsig
    ) internal pure returns (MLDSA65_PolyVec.PolyVecK memory w) {
        w = dpk.t1;

        // Щоб прибрати warning про невикористані змінні:
        dsig.c;
        dsig.z;
        dsig.h;

        return w;
    }
}
