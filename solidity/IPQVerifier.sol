// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPQVerifier {
    function verify(
        bytes calldata pubkey,
        bytes calldata signature,
        bytes32 msgHash
    ) external view returns (bool);
}
