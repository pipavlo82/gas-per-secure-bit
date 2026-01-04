// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "forge-std/console2.sol";

/// Minimal "relay attestation surface" harness:
/// - we model the on-chain cost of accepting an attestation blob
/// - we do minimal parsing + hashing so it's not a no-op
/// - we log gas in a parseable form:
///   "attestation::relay_attestation_surface gas: <N>"
contract RelayAttestationSurface {
    function touch(bytes calldata attestation) external pure returns (bytes32) {
        // Minimal "processing": hash the attestation.
        // This is a placeholder surface until the threat model / real verification is pinned.
        return keccak256(attestation);
    }
}

contract ProtocolRelayAttestationSurface_Gas_Test is Test {
    RelayAttestationSurface s;

    // Fixed-size dummy blob (adjust if you want a specific size model)
    bytes internal att;

    function setUp() public {
        s = new RelayAttestationSurface();

        // Example: 512 bytes payload (can be changed).
        att = new bytes(512);
        // make it non-trivial
        att[0] = 0x01;
        att[31] = 0x02;
        att[511] = 0x03;
    }

    function test_relay_attestation_surface_gas() public view {
        uint256 g0 = gasleft();
        bytes32 out = s.touch(att);
        uint256 used = g0 - gasleft();

        // prevent "unused"
        out;

        console2.log("attestation::relay_attestation_surface gas:", used);
    }
}
