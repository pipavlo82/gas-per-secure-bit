// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

contract ProtocolRelayAttestationSurface_Gas_Test is Test {
    uint256 internal pk;
    address internal signer;

    function setUp() public {
        pk = 0xA11CE; // deterministic test key
        signer = vm.addr(pk);
    }

    function test_relay_attestation_surface_gas() public {
        // Model: relay/builder attests to an ordering/inclusion commitment.
        bytes32 commitment = keccak256(abi.encodePacked("relay_attestation", uint256(123), bytes32(uint256(456))));

        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, commitment);
        address rec = ecrecover(commitment, v, r, s);

        // sanity
        assertEq(rec, signer);
    }
}
