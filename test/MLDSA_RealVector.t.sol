// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../solidity/MLDSA65Verifier.sol";

contract MLDSA_RealVector_Test is Test {
    MLDSA65Verifier verifier;

    function setUp() public {
        verifier = new MLDSA65Verifier();
    }

    function test_real_vector() public {
        // Load JSON from file
        string memory json = vm.readFile("test_vectors/vector_001.json");

        // Raw PQ signature from JSON
        bytes memory sig = vm.parseJsonBytes(json, ".signature_raw");

        // Raw PQ pubkey from JSON
        bytes memory pk  = vm.parseJsonBytes(json, ".public_key_raw");

        // msg_hash is stored as hex string → convert to bytes32
        string memory msgHex = vm.parseJsonString(json, ".msg_hash");
        bytes32 msgHash = bytes32(vm.parseBytes(msgHex));

        // Call verifier
        bool ok = verifier.verify(sig, msgHash, pk);

        // Since crypto verification is not implemented:
        assertFalse(ok);
    }
}
