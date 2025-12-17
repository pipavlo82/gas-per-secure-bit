// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test, console2 as console} from "../lib/forge-std/src/Test.sol";
import {Falcon} from "../src/Falcon.sol";
import {MockFalconData} from "./mocks/MockFalconData.sol";

contract Falcon_GasMicro_Test is Test {
    Falcon internal falcon;
    MockFalconData internal mockData;

    function setUp() public {
        falcon = new Falcon();
        mockData = new MockFalconData();
    }

    /// @dev Clean microbench: Falcon.verifySignature only (loads pk via loadPublicKey)
    function test_falcon_verify_gas_log() public {
        uint256 n = mockData.mockDataSetsLength();
        require(n > 0, "MockFalconData: empty");

        uint256 which = 0;

        (bytes memory signature, bytes memory publicKeyBytes) = mockData.getSignatureAndPublicKey(which);
        bytes memory domain = mockData.getDomain();
        bytes32 userOpHash = mockData.getUserOpHash(which);

        uint16[1024] memory h = falcon.loadPublicKey(publicKeyBytes);

        uint256 g0 = gasleft();
        bool ok = falcon.verifySignature(signature, userOpHash, domain, h);
        uint256 used = g0 - gasleft();

        console.log("gas_falcon_verify: %s", used);
        console.log("falcon_verified: %s", ok);
        assertTrue(ok);
    }
}
