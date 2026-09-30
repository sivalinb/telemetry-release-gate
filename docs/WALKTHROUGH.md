# Learning walkthrough

## Guided experiment

1. Open Release gate and choose Fixture analysis.
2. Run healthy; the decision should be PASS.
3. Run unexpected_label, missing_metric, and cardinality; each should BLOCK for an explicit reason.
4. Inspect Generated config and export the Collector YAML.
5. Install/start Apple Container and pre-pull the three images listed below.
6. Select Live Apple Container and run each scenario. Evidence includes the actual Prometheus query result.
7. Upload a .prom file to validate observed service telemetry. Edit the contract to reflect the target's metric names and labels.

## Questions to answer in your portfolio write-up

1. What concrete failure does this experiment expose?
2. Which checks happen before execution, and which need runtime observations?
3. Which input, configuration, image, and model versions were used?
4. What did the positive and negative controls demonstrate?
5. Where could the measurements be misleading?
6. Which follow-up experiment would challenge your conclusion?

## Suggested demonstration

Record a three-minute walkthrough: explain the failure in one sentence, run a baseline, introduce one deliberate change, inspect the evidence, and explain the tradeoff. Include the downloadable report and the command needed to reproduce it. Prefer measured operational behavior over an unsupported claim of production readiness.

## Next extensions

Add one extension only after retaining a passing baseline: more realistic public workloads, an additional failure mode, stricter provenance, a larger evaluation set, or a runtime-version comparison. Preserve fixture/live distinctions and document negative results. The other four repositories in this portfolio can reuse the report schema without creating a runtime dependency on each other.
