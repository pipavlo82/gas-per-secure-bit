// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../contracts/verifier/MLDSA65_Verifier_v2.sol";

/// @notice Harness для тестування synthetic A·z (w-обчислення).
contract MLDSA_MatrixVec_Harness is MLDSA65_Verifier_v2 {
    /// @dev Публічно експонуємо _expandA_poly для тестів.
    function exposedExpandApoly(
        bytes32 rho,
        uint8 row,
        uint8 col
    ) external pure returns (int32[256] memory) {
        return _expandA_poly(rho, row, col);
    }

    /// @dev Публічно експонуємо _compute_w, підкладаючи synthetic dpk/dsig.
    function exposedComputeW(
        bytes32 rho,
        MLDSA65_PolyVec.PolyVecL memory z
    ) external pure returns (MLDSA65_PolyVec.PolyVecK memory) {
        DecodedPublicKey memory dpk;
        dpk.rho = rho;

        DecodedSignature memory dsig;
        dsig.z = z;

        return _compute_w(dpk, dsig);
    }
}

/// @notice Тести для synthetic w = A·z.
contract MLDSA_MatrixVec_Test is Test {
    MLDSA_MatrixVec_Harness internal harness;

    function setUp() public {
        harness = new MLDSA_MatrixVec_Harness();
    }

    /// @dev Якщо z = 0, то w має бути нульовим (лінійність).
    function test_matrixvec_zero_z_yields_zero_w() public {
        bytes32 rho = bytes32(uint256(0x1234));
        MLDSA65_PolyVec.PolyVecL memory z; // за замовчуванням всі нулі

        MLDSA65_PolyVec.PolyVecK memory w = harness.exposedComputeW(rho, z);

        for (uint256 k = 0; k < MLDSA65_PolyVec.K; ++k) {
            for (uint256 i = 0; i < 256; ++i) {
                assertEq(
                    int256(w.polys[k][i]),
                    int256(0),
                    "w should be zero for zero z"
                );
            }
        }
    }

    /// @dev Unit basis: якщо z має одиницю в одній координаті,
    ///      w[k][i0] == A[k,j0][i0], а інші коефицієнти 0.
    function test_matrixvec_unit_basis_matches_expandA() public {
        bytes32 rho = bytes32(uint256(0xDEADBEEF));

        uint8 j0 = 2;
        uint16 i0 = 7;

        MLDSA65_PolyVec.PolyVecL memory z;
        z.polys[j0][i0] = int32(1);

        MLDSA65_PolyVec.PolyVecK memory w = harness.exposedComputeW(rho, z);

        for (uint8 k = 0; k < MLDSA65_PolyVec.K; ++k) {
            int32[256] memory aRow = harness.exposedExpandApoly(rho, k, j0);

            for (uint256 i = 0; i < 256; ++i) {
                int32 expected = (i == i0) ? aRow[i0] : int32(0);

                assertEq(
                    int256(w.polys[k][i]),
                    int256(expected),
                    string(
                        abi.encodePacked(
                            "w mismatch at row=",
                            vm.toString(k),
                            ", i=",
                            vm.toString(i)
                        )
                    )
                );
            }
        }
    }
}
