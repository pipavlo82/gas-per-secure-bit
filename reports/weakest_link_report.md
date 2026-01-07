# Weakest-link analysis (AA / protocol envelope dominance)

This report is generated from `data/results.jsonl`.

## Model

- For a pipeline record with dependencies (`depends_on`), define:
  - `effective_security_bits = min(security_bits(dep_i))` over all dependencies.
- `security_bits(x)` is taken from records with `security_metric_type` in `{security_equiv_bits, lambda_eff, H_min}`.

## Findings

| Record | Chain | Declared bits | Depends on | Effective bits |
|---|---|---:|---|---:|
| `falcon1024::qa_handleOps_userop_foundry_weakest_link_sigproto` | EVM/L1 | 256.0 | sigproto::eip7932_precompile_assumption | 256.0 |

## Notes

- Add explicit `depends_on` edges to reflect real execution paths (e.g., AA user op → L1 envelope).
- Keep baseline envelope assumptions as separate records (e.g., `ecdsa::l1_envelope_assumption`).
- Entropy/attestation surfaces should use `security_metric_type=H_min` with an explicit threat model in `notes`.

