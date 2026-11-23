# Generated Amadeus catalog bundle

This directory contains a generated review snapshot of the maintained Amadeus
catalogs. Edit the reviewed family YAML in the parent Amadeus repository's
`global_dataset_catalogs/`, then regenerate; do not edit generated records here.
The global catalog is assembled from those family records, not maintained as a
second independent inventory.

| Path | Contents |
|---|---|
| `global_dataset_catalogs/` | Full family and assembled global catalogs in YAML, JSON and RDS. |
| `validated_catalog_handles/` | Family discovery projections in YAML and the assembled global catalog in YAML/JSON. |
| `amadeus_schema.schema.json` | JSON Schema generated from the maintained LinkML schema. |
| `catalog_validation.json` | Validation result, counts, parity checks and retained scientific-evidence checks. |
| `catalog_build_manifest.json` | Generator-recorded input/context checksums, catalog output checksums and environment versions. |
| `metadata_gap_report.json` | Explicit binding metadata gaps and grid CRS readiness; not observation QA. |

## Regenerate and validate

Run these commands from the **parent `amadeus/` repository root**, with
`amadeus_schema/` checked out beneath it. This snapshot uses the existing
Python 3.12 `.venv-catalog` environment and dependencies pinned in
`dataset_spec_objects/catalog_requirements.txt`. R with `yaml` and `jsonlite`
is also required for lossless RDS generation and validation.

```sh
.venv-catalog/bin/python -B dataset_spec_objects/catalog_workflow.py generate \
  --output-dir amadeus_schema/build/catalog

.venv-catalog/bin/gen-json-schema \
  amadeus_schema/src/amadeus_schema/schema/amadeus_schema.yaml \
  > amadeus_schema/build/catalog/amadeus_schema.schema.json

.venv-catalog/bin/python -B dataset_spec_objects/catalog_workflow.py validate \
  --catalog-root amadeus_schema/build/catalog --native-evidence \
  --report amadeus_schema/build/catalog/catalog_validation.json
```

Stop if any command fails. Generate into a fresh output directory when dataset
membership changes, so obsolete files cannot survive from an earlier build.
The manifest hashes the catalog artifacts and schema source inputs; it does
not hash every companion file in this directory.

Generation is offline: it reuses reviewed YAML and retained provider evidence.
It does not download environmental arrays or refresh provider inventories.
A PASS result establishes the implemented metadata, reference, evidence and
serialization checks; it does not certify scientific completeness or successful
R/DuckDB/Sedona execution. The companion JSON Schema comes from the same schema
sources and generator environment; existing schema/SQL outputs in `build/`
are separate artifacts and are not rebuilt by these commands.

The generation code and retained evidence currently live in the parent
repository. This bundle alone cannot regenerate itself from a standalone
`amadeus_schema` checkout. It is prepared for review; generation does not
commit, push or refresh Amadeus's packaged `inst/catalog/` snapshot.
