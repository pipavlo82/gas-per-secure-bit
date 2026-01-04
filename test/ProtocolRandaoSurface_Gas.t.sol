// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "forge-std/console2.sol";

contract RandaoSurface {
    function touch() external view returns (bytes32) {
        // L1 entropy surface: EIP-4399 prevrandao.
        bytes32 x = bytes32(block.prevrandao);

        // Мінімальна обробка, щоб це не було "порожнє" читання.
        // (і щоб оптимізатор не мав підстав прибрати роботу)
        return keccak256(abi.encodePacked(x));
    }
}

contract ProtocolRandaoSurface_Gas_Test is Test {
    RandaoSurface s;

    function setUp() public {
        s = new RandaoSurface();
    }

    function test_l1_randao_mix_surface_gas() public view {
        // ВИМІРЮЄМО ЛИШЕ ТІЛО surface-операції (log-isolated):
        // очікуваний лог для парсера:
        //   "randao::l1_randao_mix_surface gas: <N>"

        uint256 g0 = gasleft();
        bytes32 out = s.touch();
        uint256 used = g0 - gasleft();

        // щоб результат не був "unused" (і не було умовної оптимізації)
        out;

        console2.log("randao::l1_randao_mix_surface gas:", used);
    }
}
