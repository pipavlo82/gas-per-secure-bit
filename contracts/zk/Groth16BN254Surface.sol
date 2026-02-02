// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Minimal BN254 pairing surface (Groth16-like shape).
/// We measure "pairing(4 pairs)" cost using the BN254 precompile at 0x08.
/// Input is 4 pairs of point-at-infinity encodings (all-zero), which is valid and should return 1.
contract Groth16BN254Surface {
    address constant PAIRING = address(0x08);

    /// Pairing-only surface: 4 pairs (4 * 6 words).
    function pairing4_zero() external view returns (bool ok) {
        // 4 pairs * 6 words * 32 bytes = 768 bytes
        bytes memory input = new bytes(24 * 32);

        (bool s, bytes memory out) = PAIRING.staticcall(input);
        if (!s || out.length != 32) return false;

        ok = (abi.decode(out, (uint256)) == 1);
    }
}
