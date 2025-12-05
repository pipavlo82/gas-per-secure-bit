// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

contract MLDSA_RealVector_Test is Test {
    string constant SIG_PATH = "signature_clean2.txt";
    string constant PK_PATH  = "pubkey_final.txt";
    string constant MSG_PATH = "msg_clean2.txt";

    bytes signature;
    bytes pubkey;
    bytes msgHash;

    function setUp() public {
        signature = vm.readFileBinary(SIG_PATH);
        pubkey    = vm.readFileBinary(PK_PATH);
        msgHash   = vm.readFileBinary(MSG_PATH);
    }

    function test_LoadVectors() public view {
        require(signature.length > 0, "signature empty");
        require(pubkey.length > 0, "pubkey empty");
        require(msgHash.length > 0, "msg empty");
    }
}
