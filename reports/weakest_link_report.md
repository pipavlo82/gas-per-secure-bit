# Weakest-link analysis (AA / protocol envelope dominance)

This report is generated from `data/results.jsonl`.

## Model

- For a pipeline record with dependencies (`depends_on`), define:
  - `effective_security_bits = min(security_bits(dep_i))` over all dependencies.
- `security_bits(x)` is taken from records with `security_metric_type` in `{security_equiv_bits, lambda_eff, H_min}`.

## Findings

No records with `security_model=weakest_link` or non-empty `depends_on` were found.
Add `depends_on` to AA/UserOp benchmarks to compute end-to-end effective security.
