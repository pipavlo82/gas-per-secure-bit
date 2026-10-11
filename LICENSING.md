# Licensing scope

The Apache License, Version 2.0, reproduced in [LICENSE](LICENSE), applies to
Pavlo-authored repository material within the scope below, to the extent Pavlo
owns or is authorized to license the relevant rights.

Copyright 2026 Pavlo Tvardovskyi

Existing third-party copyright, license, patent, attribution and trademark
notices remain applicable. For mixed or adapted material, the new grant covers
only Pavlo's original additions. Imported source, external contributions,
quoted specifications, captures and other third-party material are not
relicensed by this grant. Inclusion in this repository or a missing license
does not itself supply permission. Existing grants are not withdrawn or narrowed.

| Material | Applicable boundary |
| --- | --- |
| Pavlo-authored scripts, benchmark harness additions, contracts, specifications, configuration and original analysis/documentation | Apache-2.0 for Pavlo's original contributions. Existing MIT source grants remain available; they are not withdrawn by this additional owner grant. |
| `bench/ecdsa/lib/forge-std/**` | Imported Forge Standard Library; retain `LICENSE-APACHE`, `LICENSE-MIT`, package metadata, source headers and original author notices. Its dual license remains unchanged. |
| `lib/forge-std` | Separate pinned submodule; original upstream terms apply. Its gitlink, `.gitmodules` and `foundry.lock` are unchanged and it was not initialized for this cleanup. |
| Generated/default Foundry template files, third-party snippets or interfaces under `bench/**`, `contracts/**`, `solidity/**` and `test/**` | Existing per-file SPDX/attribution and template rights remain applicable; this grant covers only Pavlo's original additions, not unconfirmed template authorship. Historical UNLICENSED template markers are not converted into an asserted Pavlo grant. |
| `data/**`, `reports/**`, `research/**`, `vectors/**`, `test_vectors/**` and referenced vendor measurements | Original compilation/analysis is covered only where Pavlo owns it. Imported vectors, captured logs, source excerpts and third-party benchmark records retain source rights. Keep recorded repository/commit identities; no new grant for an unlicensed vendor is implied. |

The README's earlier MIT-only badge is replaced with the current default
Apache-2.0 grant. Existing MIT permissions on source material remain intact.
Referenced vendor repositories are separate works, not relicensed here. No
measurement, report, vector, dependency pin, package metadata or source header
is changed by this legal cleanup.
