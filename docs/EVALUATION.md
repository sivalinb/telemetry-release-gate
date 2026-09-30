# Evaluation methodology

The positive control includes two request series and one queue series. Negative controls independently change labels, cardinality, metric presence, types, numeric values, and duplicate identities. A block is a successful evaluation outcome for an intentionally invalid fixture. Live verification must additionally confirm that the backend query contains the producer's samples. No cost savings or production-scale ingestion claim follows from this bounded test.

## Portable automated checks

Run `pytest -q` and `python scripts/evaluate.py`. Pytest covers independent expected outcomes and boundary conditions, while Streamlit AppTest drives a visible workflow and checks for uncaught exceptions. Pkl tests exercise valid configuration and the Python suite rejects invalid configuration/inputs. The retrieval evaluation uses hand-authored held-out questions, expected evidence IDs, top-three hit rate, and an unrelated question requiring abstention.

## Live verification

Run `python scripts/run.py --live` where supported on an Apple silicon Mac. Live work is intentionally excluded from ordinary Linux CI. A manual macOS workflow is supplied for an explicitly provisioned self-hosted runner. Review the checkout before running it; no pull-request trigger dispatches arbitrary code onto a personal Mac.

## Reporting

Keep the actual pass/fail result, sample count, environment, and raw evidence. A failed negative-control workload may be the expected test outcome; a failed runtime setup is not. Synthetic fixtures test logic, not real-world performance. Simulation invariants do not establish production guarantees. Local model quality scores are bounded by the prompt sample and scoring rule. Retrieval hit rate does not measure generated-answer factuality.
