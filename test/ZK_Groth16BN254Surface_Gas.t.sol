// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "forge-std/console2.sol";

import "../contracts/zk/Groth16BN254Surface.sol";

contract ZK_Groth16BN254Surface_Gas is Test {
    function test_gas_groth16_bn254_pairing4_surface() public {
        Groth16BN254Surface s = new Groth16BN254Surface();

        uint256 g0 = gasleft();
        bool ok = s.pairing4_zero();
        uint256 used = g0 - gasleft();

        // we don't care about "truth" here; only that the call succeeded.
        assertTrue(ok);

        console2.log("gas_groth16_bn254_pairing4_surface", used);
    }
}
