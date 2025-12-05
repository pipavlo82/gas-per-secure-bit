// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPQVerifier {
    function verify(
        bytes32 msgHash,
        bytes calldata signature,
        bytes calldata pubKey
    ) external view returns (bool ok);
}
