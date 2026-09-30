# Security and limitations

The live stack consumes roughly 1.25–2 GB of guest allocations and pulls images on first use. Exporter translation can change metric names across versions; images are versioned and the resulting exposition is validated. Pkl validates configuration, not runtime data. Uploaded exposition is a point-in-time observation, not a rate or a full historical cardinality estimate. Unit governance is expressed in naming/conventions in this version; it does not infer physical units from raw sample values.

## Shared boundaries

The app is intended for a trusted local user. It has no multi-user authentication or tenant isolation at the Streamlit layer. Public deployment requires a separate access-control and execution-service design. The Pkl evaluator only loads the repository's trusted module. Public sources are allowlisted and not executed. Input sizes, resource settings, subprocess output, and execution durations are bounded where implemented. The detailed report distinguishes active enforcement from documentation and experimental assumptions.

Source and model content may include misleading instructions; retrieval and model outputs have no authority to change application policy. Citation membership alone does not prove correctness. Never publish private production logs or credentials as example data. Report suspected security defects privately through the repository owner's GitHub contact channels; do not include working credentials in an issue.
