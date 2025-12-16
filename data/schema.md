# Dataset schema (v0)

We store results in:
- data/results.jsonl (append-only)
- data/results.csv (generated view)

JSONL fields (v0):
- ts_utc
- repo
- commit
- scheme
- bench_name
- chain_profile
- gas_verify
- security_metric_type
- security_metric_value
- gas_per_secure_bit
- hash_profile
- notes
