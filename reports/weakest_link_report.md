# Weakest-link analysis (AA / protocol envelope dominance)

This report is generated from `data/results.jsonl`.

## Model

- For a pipeline record with dependencies (`depends_on`), define:
  - `effective_security_bits = min(security_bits(dep_i))` over all dependencies.
- `security_bits(x)` is taken from records with `security_metric_type` in `{security_equiv_bits, lambda_eff}`.

## Findings

| Record | Chain | Declared bits | Depends on | Effective bits |
|---|---|---:|---|---:|
| `falcon1024::qa_handleOps_userop_foundry_weakest_link` | EVM/L1 | 256.0 | ecdsa::l1_envelope_assumption, falcon1024::qa_handleOps_userop_foundry | 128.0 |
| `falcon1024::qa_validateUserOp_userop_log_weakest_link` | EVM/L1 | 256.0 | ecdsa::l1_envelope_assumption, falcon1024::qa_validateUserOp_userop_log | 128.0 |

## Notes

- Add explicit `depends_on` edges to reflect real execution paths (e.g., AA user op → L1 envelope).
- Keep baseline envelope assumptions as separate records (e.g., `ecdsa::l1_envelope_assumption`).

