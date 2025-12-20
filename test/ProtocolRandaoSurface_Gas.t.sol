// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

contract RandaoSurface {
    function touch() external view returns (bytes32) {
        // L1 entropy surface: EIP-4399 prevrandao.
        bytes32 x = bytes32(block.prevrandao);
        // мінімальна обробка, щоб не було "порожнього" читання
        return keccak256(abi.encodePacked(x));
    }
}

contract ProtocolRandaoSurface_Gas_Test is Test {
    RandaoSurface s;

    function setUp() public {
        s = new RandaoSurface();
    }

    function test_l1_randao_mix_surface_gas() public view {
        s.touch();
    }
}
