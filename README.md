# Telemetry Release Gate

[![Verify](https://github.com/sivalinb/telemetry-release-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/sivalinb/telemetry-release-gate/actions/workflows/ci.yml)

A service can build successfully while emitting telemetry that breaks dashboards or creates an unbounded number of series. This application treats a telemetry contract as a release criterion.

Python · Streamlit · Pkl · Apple Container · evaluation evidence · OpenTelemetry

## Start here

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py --server.port 8501
```

The interface opens at http://127.0.0.1:8501. Portable demos work without a model, API key, Pkl executable, or container runtime. The configuration fallback is a checked export whose source hash must match the committed Pkl source. Every report identifies its mode.

## Walkthrough

1. Open Release gate and choose Fixture analysis.
2. Run healthy; the decision should be PASS.
3. Run unexpected_label, missing_metric, and cardinality; each should BLOCK for an explicit reason.
4. Inspect Generated config and export the Collector YAML.
5. Install/start Apple Container and pre-pull the three images listed in [Setup](docs/SETUP.md).
6. Select Live Apple Container and run each scenario. Evidence includes the actual Prometheus query result.
7. Upload a .prom file to validate observed service telemetry. Edit the contract to reflect the target's metric names and labels.

## Architecture

Pkl contract → Python contract model → exposition parser → label/type/series checks → release decision. Live mode adds a Python OTLP producer → OpenTelemetry Collector → Prometheus and verifies the query result.

The Streamlit UI calls pure Python engines; each repository vendors a small `labcore` package so cloning this repository is sufficient. No sibling repository is required.

## CLI and checks

```bash
python scripts/run.py --case healthy
python scripts/run.py --case cardinality
python scripts/run.py --live --case healthy
pytest -q
python scripts/evaluate.py
python scripts/export_config.py   # requires pkl on PATH or PKL_BIN
```

## Observed verification

26 automated tests passed locally. A real OTLP → Collector → Prometheus pipeline passed its healthy contract and blocked all three injected telemetry faults. See [verified results and evidence](docs/VALIDATION.md) for settings, provenance, and limitations.

## Documentation

- [Setup and live runtime](docs/SETUP.md)
- [Architecture and decisions](docs/ARCHITECTURE.md)
- [Learning walkthrough](docs/WALKTHROUGH.md)
- [Evaluation methodology](docs/EVALUATION.md)
- [Public sources and licenses](docs/DATA_SOURCES.md)
- [Observability and AI](docs/OPERATIONS.md)
- [Security and limitations](docs/SECURITY.md)
- [Verified results](docs/VALIDATION.md)

MIT-licensed project code. External datasets and references retain their own terms. Public inputs are fetched explicitly and kept under ignored `artifacts/`; no private production telemetry is included.
