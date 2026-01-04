// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

contract ProtocolDASSampleSurface_Gas_Test is Test {
    // “Verify one DAS sample (512 bytes)” surface.
    // Model: commitment = keccak256(sample); verify == recompute hash & compare.
    function verifySample(bytes calldata sample, bytes32 commitment) external pure returns (bool) {
        return keccak256(sample) == commitment;
    }

    function test_gas_das_verify_sample_512b_surface() public {
        bytes memory sample = new bytes(512);
        // deterministic fill (avoid randomness dependence)
        for (uint256 i = 0; i < sample.length; i++) {
            sample[i] = bytes1(uint8(i));
        }
        bytes32 commitment = keccak256(sample);

        uint256 g0 = gasleft();
        bool ok = this.verifySample(sample, commitment); // external call => realistic calldata path
        uint256 used = g0 - gasleft();

        assertTrue(ok);
        emit log_named_uint("das::verify_sample_512b_surface gas", used);
    }
}
