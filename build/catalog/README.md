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

## Earlier GOES-ADP update

The earlier JSON update added only NOAA GOES-ADP: satellites 16/18, sectors C/F/M, and
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

## MODIS/VIIRS catalog update

The MODIS JSON catalog now covers all 38 downloader short names in 41 product
profiles and 372 variable bindings. The original seven profiles and 64 bindings
are preserved; 33 additional short names contribute 34 profiles and 308 bindings.
The family registry remains at 24 families. Both global JSON catalogs contain
the regenerated full union, now totaling 353 products. Other family JSON files
are unchanged.

Thirty-six short names have version-matched CMR collection evidence. MCD14ML
and MCD64CMQ use documented NASA/UMD identities without invented CMR identifiers.
All 308 new bindings retain `under_investigation`: catalog registration does not
certify native decoding, QA application, authenticated access, or existing R
processing compatibility. Unresolved CRS and format declarations remain explicit.

This update stages only JSON catalogs, the refreshed build/validation/gap reports,
and this README. YAML/RDS remain local generation and parity-validation artifacts.
The existing schema, processing code, and unrelated catalog definitions are not
part of the update. Source evidence, scientific decisions, and execution limits
are documented in the parent repository's
`dataset_spec_objects/modis_viirs_intake_20261124/README.md`.

## MERRA-2 temporal and adapter review (2026-11-28)

The MERRA-2 family retains 95 Products (93 native collections and two derived
GlobalFWI discovery Products) and 2,673 bindings. Live NASA collection identities
and all 93 exact variable dictionaries were reviewed. This update adds 32
missing collection coverage starts, 10 documented hourly timestamp alignments,
and 32 download registrations matching the current Amadeus lookup. Monthly and
diurnal processing routes are not added. All other family definitions are
unchanged; the global catalogs are the regenerated full union.

Two specification-backed bindings absent by exact name from the live
dictionaries remain flagged: `inst3_3d_gas_Nv.DELP` (the dictionary lists `delp`)
and `tavg1_2d_adg_Nx.DUSV001`. No bindings, units or canonical identities are
deleted or inferred. The parent checkout retains the responses, checksums,
implementation snapshots and full review in
`dataset_spec_objects/merra2_temporal_review_20261128/`.

The strict workflow now records the exact saved schema artifact's SHA-256 in
both the manifest and validation report. Schema constraints and version are
unchanged; serialization of the artifact is controlled by that workflow.
Its PASS covers strict JSON/schema/version/hash, union, reference, privacy,
format, RDS and retained-evidence checks. Separate checkmate validation passes
all 5,269 MERRA-2 records, but finds 18 pre-existing failures on unchanged global
assets (fractional-second datetime patterns and large integer checks). These
additional failures are reported separately and are not represented as a pass.
The working Amadeus `inst/catalog/` release snapshot is not republished.

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

.venv-catalog/bin/python -B dataset_spec_objects/catalog_workflow_2.py generate \
  --output-dir amadeus_schema/build/catalog \
  --schema-artifact amadeus_schema.schema.json

.venv-catalog/bin/python -B dataset_spec_objects/catalog_workflow_2.py validate \
  --catalog-root amadeus_schema/build/catalog --native-evidence \
  --schema-artifact amadeus_schema/build/catalog/amadeus_schema.schema.json \
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
