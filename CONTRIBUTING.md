# Contributing

## Add a new vendor benchmark (runner)

1) Create a runner script in `scripts/`:
   - `scripts/run_vendor_<name>.sh`
   - It should output JSON to stdout or call `scripts/parse_bench.py` with a JSON payload.

2) Required fields per record:
   - scheme, bench_name, gas, security_metric_type, security_equiv_bits (or H_min)
   - provenance: repo + commit of the *vendored* implementation (not this repo)

3) Verify:
   - `python3 scripts/parse_bench.py < payload.json`
   - `bash scripts/make_reports.sh`

4) Submit:
   - PR with runner + one example record + docs update.
