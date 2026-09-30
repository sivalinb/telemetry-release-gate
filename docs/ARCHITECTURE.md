# Architecture

## Data flow

Pkl contract → Python contract model → exposition parser → label/type/series checks → release decision. Live mode adds a Python OTLP producer → OpenTelemetry Collector → Prometheus and verifies the query result.

## Implementation decisions

The checker enforces all explicitly declared metrics and flags undeclared lab_* metrics. Generated batch settings and scrape intervals come from Pkl. Missing-metric and cardinality Prometheus rules are generated from the same contract. This avoids treating Collector self-observability as application metrics. Contract entries must have unique names, valid types, nonempty ownership, required-label subsets, and finite cardinality budgets. Counter family names are normalized by prometheus_client's parser; checks apply to emitted sample names. Unknown lab_* metrics, duplicate series, wrong types, negative counters, nonfinite values, missing labels, and budget violations produce findings. The schema currently supports counters and gauges; histogram and summary contracts are a documented extension, not silently accepted.

## Modules

`app.py` renders Streamlit controls and stores the current report in session state. `engine.py` contains domain logic and typed runtime models. `config/` stores Pkl source and its verified export. `labcore/runtime.py` issues argument-array subprocess calls, captures bounded output, and scopes cleanup to generated job names. `labcore/observability.py` writes event metadata and experiment reports. `labcore/ai.py` retrieves reference evidence and optionally synthesizes a cited answer. `data/sources.json` declares the public inputs and their terms. `workloads/` contains trusted workload entrypoints, where needed. `tests/` covers failure cases and Streamlit workflows.

## Trust boundaries

UI uploads and downloaded source content are data. They do not become system commands or Pkl modules. The sandbox project explicitly permits user Python inside a VM. Other tools execute only checked-in workload entrypoints. Subprocess calls use argument lists without a shell. Source URLs come from a fixed HTTPS catalogue with redirects disabled. Model responses are advisory and cannot trigger container actions.

## Persistence and reproducibility

Run artifacts are local and ignored by Git. Reports retain the mode, input/contract settings, source/config hashes where applicable, raw observations, and calculated decisions. Reproduce a finding by saving the report, pinning runtime/image/model versions, rerunning with the same workload, and comparing independent trials. Generated configuration and dependency versions are committed. For formal benchmarks replace mutable image tags with verified OCI digests.
