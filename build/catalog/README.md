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

## GOES-ADP update

The JSON set adds only NOAA GOES-ADP: satellites 16/18, sectors C/F/M, and
separate Baseline/Enterprise algorithm profiles. Existing family definitions
are unchanged. The published subset contains JSON; local YAML/RDS files are
generation and validation artifacts and are not included in this commit.
The schema and three reports listed above remain at this directory's root.
They are not duplicated inside `validated_catalog_handles/`.

`global_dataset_catalogs/goes.json` contains the full definitions.
`validated_catalog_handles/goes.json` is the optional discovery projection;
see that directory's README. Both global JSON files contain the assembled full
union, preserving the existing layout. The JSON Schema is unchanged by GOES
registration and is already tracked.

## Regenerate and validate

Run these commands from the **parent `amadeus/` repository root**, with
`amadeus_schema/` checked out beneath it. This snapshot uses the existing
Python 3.12 `.venv-catalog` environment and dependencies pinned in
`dataset_spec_objects/catalog_requirements.txt`. R with `yaml` and `jsonlite`
is also required for lossless RDS generation and validation.

```sh
mkdir -p amadeus_schema/build/catalog/validated_catalog_handles
# Request the existing generator's optional GOES discovery JSON output.
touch amadeus_schema/build/catalog/validated_catalog_handles/goes.json

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
Its output hashes describe the complete generated YAML/JSON/RDS build, including
the optional GOES handle JSON. A JSON-only checkout does not contain every file
listed in that full-build manifest; regenerate the complete tree before running
serialization-parity validation.

Generation is offline: it reuses reviewed YAML and retained provider evidence.
It does not download environmental arrays or refresh provider inventories.
A PASS result establishes the implemented metadata, reference, evidence and
serialization checks; it does not certify scientific completeness or successful
R/DuckDB/Sedona execution. The companion JSON Schema comes from the same schema
sources and generator environment; existing schema/SQL outputs in `build/`
are separate artifacts and are not rebuilt by these commands.
All 48 GOES bindings retain explicit investigation flags. Existing R adapters
do not apply all required algorithm-specific QA screens or guarantee categorical
resampling; these catalogs do not certify quantitative aerosol exposure.

The generation code and retained evidence currently live in the parent
repository. This bundle alone cannot regenerate itself from a standalone
`amadeus_schema` checkout. It is prepared for review; generation does not
commit, push or refresh Amadeus's packaged `inst/catalog/` snapshot.
