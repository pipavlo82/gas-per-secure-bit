// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

contract ProtocolRandaoSamplingSurface_Gas_Test is Test {
    function deriveIndices(uint256 n, uint256 range) external view returns (uint256 acc) {
        // acc is just to prevent optimizer from dropping the loop
        uint256 seed = uint256(block.prevrandao);

        for (uint256 i = 0; i < n; i++) {
            seed = uint256(keccak256(abi.encodePacked(seed, i)));
            acc ^= (seed % range);
        }
        return acc;
    }

    function test_gas_randao_mix_for_sample_selection_surface() public {
        uint256 n = 16;        // number of samples
        uint256 range = 4096;  // e.g., “cells” / “indices” universe; tweakable

        uint256 g0 = gasleft();
        uint256 out = this.deriveIndices(n, range);
        uint256 used = g0 - gasleft();

        // prevent dead-code elimination
        assertTrue(out | 1 == out + 1 || out | 1 == out);

        emit log_named_uint("randao::mix_for_sample_selection_surface gas", used);
    }
}
