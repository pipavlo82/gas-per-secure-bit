// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ECDSA1271Wallet {
    // ERC-1271 magic value
    bytes4 internal constant MAGICVALUE = 0x1626ba7e;

    address public immutable owner;

    constructor(address _owner) {
        owner = _owner;
    }

    /// @notice ERC-1271 signature check (bytes signature, 65-byte r||s||v)
    function isValidSignature(bytes32 digest, bytes calldata signature) external view returns (bytes4) {
        if (signature.length != 65) return bytes4(0xffffffff);

        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := calldataload(signature.offset)
            s := calldataload(add(signature.offset, 32))
            v := byte(0, calldataload(add(signature.offset, 64)))
        }
        if (v < 27) v += 27;

        address recovered = ecrecover(digest, v, r, s);
        return (recovered == owner) ? MAGICVALUE : bytes4(0xffffffff);
    }
}
