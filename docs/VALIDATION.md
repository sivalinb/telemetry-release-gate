# Verified results

Verified on 2026-09-30 UTC (2026-09-29 Mountain Time). This page reports observed development checks, not production reliability guarantees. The committed JSON evidence contains synthetic workloads, public-source metadata, and measured results. Secrets, local usernames, and source-cache contents are excluded.

## Portable checks

- `pytest -q`: **26 passed**, including the Streamlit primary workflow.
- `python scripts/evaluate.py`: all domain checks passed; retrieval hit@3 was 1.0 on five authored questions, and the unrelated-question abstention check passed.
- Pkl 0.32.1: valid configuration tests passed; invalid CPU allocation is rejected by the Python test suite.
- `ruff check .`: passed.

[portable-checks.json](evidence/portable-checks.json) preserves command results. The five retrieval questions are a small diagnostic suite, not a broad RAG quality benchmark. The default reviewer performs deterministic retrieval; no LLM is required for portable checks.

[Environment and OCI digests](evidence/environment.json) identify the tested dependencies and live image revisions. [GitHub Actions](https://github.com/sivalinb/telemetry-release-gate/actions) independently reports the current portable CI status. Ordinary Linux CI does not run Apple Container workloads.

## Live pipeline results

A Python producer sent OTLP/HTTP metrics to an actual OpenTelemetry Collector VM. A separate Prometheus VM scraped the collector and returned the expected counter vector. The healthy contract passed with two request series and one queue series. All three live negative controls blocked as expected:

| Input | Observed decision | Finding |
|---|---|---|
| Healthy | PASS | No contract violations |
| Extra `user_id` label | BLOCK | Unexpected label |
| Missing queue metric | BLOCK | Required metric absent |
| 20 request series against an 8-series budget | BLOCK | Cardinality budget exceeded |

The live result is in [live-pipeline.json](evidence/live-pipeline.json); negative-control observations are in [negative-controls.json](evidence/negative-controls.json). Private VM addresses are replaced with `PRIVATE_VM_IP` in the published report. The gate covers explicitly declared metrics and unknown `lab_*` metrics. It does not claim arbitrary semantic correctness, full OpenMetrics conformance, histogram validation, or long-term backend stability.

## Reproduce

Run `python scripts/run.py --live --case healthy`, then substitute `unexpected_label`, `missing_metric`, and `cardinality`. Inspect the decision and findings, not just whether the CLI completed. Prometheus rules are generated from the contract; the live smoke trial verifies sample transport and query results, not every alert's firing interval.

## Public source verification

All ten catalogue entries downloaded successfully during verification, including USGS, NAB CPU/taxi, GSM8K, OpenMetrics, OTel semantic conventions, Pkl/Container releases, Apple runtime resource documentation, and node_exporter documentation. [public-sources.json](evidence/public-sources.json) records retrieval times, byte counts, hashes, URLs, and upstream terms. Documentation and release metadata are reference material, not empirical workload measurements. Downloaded source contents remain untracked and are not relicensed by this repository.
