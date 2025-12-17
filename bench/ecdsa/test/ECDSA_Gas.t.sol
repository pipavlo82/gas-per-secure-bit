// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/ECDSAVerifier.sol";
import "../src/ECDSA1271Wallet.sol";

contract ECDSA_Gas_Test is Test {
    ECDSAVerifier vfy;
    ECDSA1271Wallet wallet;

    uint256 sk;
    address pk;
    bytes32 digest;

    bytes sig65; // r||s||v (65 bytes)

    function setUp() public {
        vfy = new ECDSAVerifier();

        sk = 1;
        pk = vm.addr(sk);
        digest = keccak256("gas-per-secure-bit:ecdsa");

        (uint8 v, bytes32 r, bytes32 s) = vm.sign(sk, digest);
        sig65 = abi.encodePacked(r, s, v);

        wallet = new ECDSA1271Wallet(pk);
    }

    // (baseline) direct ecrecover path
    function test_ecdsa_verify_ecrecover_gas() public {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(sk, digest);
        bool ok = vfy.verify(digest, v, r, s, pk);
        require(ok, "bad sig");
    }

    // (1) bytes(65) calldata shape
    function test_ecdsa_verify_bytes65_gas() public {
        bool ok = vfy.verifyBytes(digest, sig65, pk);
        require(ok, "bad sig");
    }

    // (2) ERC-1271 flavor (wallet surface)
    function test_ecdsa_erc1271_isValidSignature_gas() public {
        bytes4 magic = wallet.isValidSignature(digest, sig65);
        require(magic == 0x1626ba7e, "bad magic");
    }
}
