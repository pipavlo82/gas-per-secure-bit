// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ECDSAVerifier {
    /// @notice Baseline ECDSA verification via ecrecover (secp256k1)
    function verify(
        bytes32 digest,
        uint8 v,
        bytes32 r,
        bytes32 s,
        address expected
    ) external pure returns (bool) {
        address recovered = ecrecover(digest, v, r, s);
        return recovered == expected;
    }

    /// @notice Verify with a 65-byte signature: r(32) || s(32) || v(1)
    function verifyBytes(
        bytes32 digest,
        bytes calldata sig,
        address expected
    ) external pure returns (bool) {
        (uint8 v, bytes32 r, bytes32 s) = _split65(sig);
        address recovered = ecrecover(digest, v, r, s);
        return recovered == expected;
    }

    function _split65(bytes calldata sig) internal pure returns (uint8 v, bytes32 r, bytes32 s) {
        require(sig.length == 65, "bad sig len");
        assembly {
            // calldata layout: sig.offset points to data
            r := calldataload(sig.offset)
            s := calldataload(add(sig.offset, 32))
            v := byte(0, calldataload(add(sig.offset, 64)))
        }
        // normalize v: allow 0/1 or 27/28
        if (v < 27) v += 27;
    }
}
