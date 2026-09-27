# Drug Discovery Data Catalog

A reproducible scientific data engineering pipeline for ingesting, standardizing, enriching, validating, and cataloging compound-target bioactivity data with end-to-end provenance.

The project integrates public drug discovery data from ChEMBL and PubChem, preserves raw source records, performs quality checks, supports resumable enrichment, and loads curated scientific data into PostgreSQL for discovery and analysis.

## Why This Project Exists

Drug discovery datasets often come from heterogeneous scientific sources with different identifiers, schemas, completeness levels, experimental contexts, and metadata conventions.

This project demonstrates a workflow for:

- integrating scientific datasets from multiple sources
- preserving raw source data
- standardizing bioactivity records
- enriching compounds across databases
- tracking source releases, provenance, and checksums
- identifying invalid, repeated, and conflicting measurements
- processing large target-specific datasets in batches
- checkpointing external API enrichment
- cataloging curated records in PostgreSQL
- supporting reproducible SQL-based data discovery

## Data Sources

### ChEMBL

ChEMBL is used for:

- compound-target bioactivity records
- molecule identifiers
- assay identifiers
- document identifiers
- activity types such as IC50, Ki, Kd, and EC50
- standardized activity values
- source release/version metadata

The full EGFR pipeline run used:

```text
ChEMBL_37
```

### PubChem

PubChem is used to enrich ChEMBL compounds with:

- PubChem CID
- molecular formula
- molecular weight
- SMILES
- connectivity SMILES
- InChI
- InChIKey
- IUPAC name

Compounds are linked across ChEMBL and PubChem using InChIKey.

## Example Target

The current pipeline example uses:

```text
CHEMBL203 — EGFR
```

EGFR is a widely studied protein target relevant to cancer drug discovery.

## Architecture

```text
                     ChEMBL
                    /      \
          activities        molecules
              |                 |
              |              InChIKey
              |                 |
              |              PubChem
              |                 |
              +--------+--------+
                       |
                       v
                normalization
                       |
                 quality checks
                       |
                 provenance
                       |
                       v
                  PostgreSQL
             /        |        \
       compounds    targets    assays
             \        |        /
              \       |       /
                 activities
```

## Pipeline

The end-to-end CLI performs the following workflow:

```text
ChEMBL API
    |
    v
paginated activity ingestion
    |
    +--> raw JSON
    +--> SHA-256 checksum
    +--> provenance manifest
    +--> ChEMBL release version
    |
    v
activity normalization
    |
    +--> rejected-record tracking
    +--> quality validation
    |
    v
unique compounds
    |
    v
batched ChEMBL molecule lookup
    |
    v
InChIKey
    |
    v
batched PubChem enrichment
    |
    +--> retry / exponential backoff
    +--> persistent enrichment cache
    +--> checkpoint after successful batches
    |
    v
duplicate/conflict analysis
    |
    v
consolidated quality report
    |
    v
PostgreSQL catalog
```

## Full EGFR Pipeline Results

The pipeline was validated end-to-end against the complete ChEMBL activity dataset returned for EGFR (`CHEMBL203`) using ChEMBL 37.

| Metric | Result |
| --- | ---: |
| Raw ChEMBL activity records | 58,847 |
| Normalized activity records | 28,643 |
| Rejected activity records | 30,204 |
| Unique compounds | 14,670 |
| PubChem-enriched compounds | 14,383 |
| Enrichment failures | 287 |
| Assays cataloged | 2,690 |
| Activity rows loaded | 28,148 |

The full-scale run processed PubChem enrichment in hundreds of batches rather than issuing one API request per compound.

Persistent checkpointing allows completed PubChem lookups to be reused if a later request fails or the pipeline is interrupted.

Raw ChEMBL data can also be reused locally so downstream processing does not require downloading the complete activity dataset again.

## Resilient Enrichment

Large scientific API workflows can fail because of transient network errors, rate limits, or upstream service availability.

The PubChem enrichment layer therefore includes:

- batched compound requests
- configurable request timeouts
- retry handling
- exponential backoff
- handling for transient HTTP `429` and `5xx` responses
- persistent local checkpoints
- reuse of successfully enriched compounds

For example, a repeated run can reuse previously cached enrichment results instead of requesting the same compounds again.

Runtime cache files are stored under:

```text
data/cache/
```

and are excluded from version control.

## Reusing Raw ChEMBL Data

A previously downloaded ChEMBL activity dataset can be reused with:

```bash
drug-catalog run \
  --target CHEMBL203 \
  --reuse-raw
```

This allows normalization, enrichment, quality analysis, and database loading to be repeated without downloading the full ChEMBL dataset again.

For development and testing, a smaller sample can still be processed using:

```bash
drug-catalog run \
  --target CHEMBL203 \
  --max-records 25
```

## Data Provenance

Every raw dataset is stored with provenance metadata including:

- source name
- source version when available
- API endpoint
- query parameters
- retrieval timestamp
- raw-file path
- SHA-256 checksum
- record count
- pipeline version

Example:

```json
{
  "run_id": "chembl-20260927T005514Z",
  "source": {
    "source_name": "ChEMBL",
    "source_version": "ChEMBL_37",
    "endpoint": "https://www.ebi.ac.uk/chembl/api/data/activity.json",
    "query_parameters": {
      "target_chembl_id": "CHEMBL203"
    }
  },
  "raw_file": {
    "record_count": 58847,
    "sha256": "..."
  },
  "pipeline_version": "0.1.0"
}
```

Raw source files remain separate from curated outputs so transformations can be reproduced and audited.

## Data Quality

The pipeline validates activity records before loading them into the curated catalog.

Current rejection categories include:

- missing molecule identifier
- missing target identifier
- unsupported activity type
- unsupported units
- missing or invalid activity value

A consolidated quality report is generated at:

```text
data/curated/CHEMBL203_quality_report.json
```

The quality report summarizes:

- raw record counts
- normalized record counts
- rejected records
- rejection reasons
- unique compounds
- successful enrichments
- enrichment failures
- repeated measurements
- exact duplicates
- conflicting measurements

## Repeated Measurements vs. Conflicts

A compound may legitimately have multiple activity measurements against the same target.

Measurements are not considered conflicting simply because their numeric values differ.

The catalog treats measurements as directly comparable only when they share the same:

- compound
- target
- assay
- activity type
- units

Measurements from different assays represent different experimental contexts and are therefore retained independently.

Conflict detection is restricted to measurements that share the same compound, target, assay, activity type, and units but report inconsistent values.

This distinction avoids incorrectly treating legitimate experimental replication or assay variation as a data-quality error.

## PostgreSQL Catalog

The relational catalog contains the following core entities.

### `sources`

Scientific source systems such as ChEMBL and PubChem, including source version and endpoint metadata.

### `ingestion_runs`

Tracks individual source retrievals, query metadata, raw-file checksums, record counts, timestamps, and pipeline versions.

### `compounds`

Cross-source compound metadata including ChEMBL identifiers, PubChem IDs, molecular properties, SMILES, and InChIKey.

### `targets`

Drug targets represented by ChEMBL target identifiers.

### `assays`

ChEMBL assay identifiers associated with targets.

### `activities`

Normalized compound-target bioactivity measurements linked to compounds, targets, assays, and ingestion runs.

## Setup

### Requirements

- Python 3.12+
- Docker
- Docker Compose
- Git

Create and activate the environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the package and development dependencies:

```bash
pip install -e ".[dev]"
```

Start PostgreSQL:

```bash
docker compose up -d
```

## Run the Pipeline

Run the complete EGFR dataset:

```bash
drug-catalog run \
  --target CHEMBL203
```

Reuse previously downloaded ChEMBL data:

```bash
drug-catalog run \
  --target CHEMBL203 \
  --reuse-raw
```

Run a small development sample:

```bash
drug-catalog run \
  --target CHEMBL203 \
  --max-records 25
```

The pipeline:

1. identifies the active ChEMBL release
2. retrieves or reuses ChEMBL activity data
3. preserves raw records and provenance
4. normalizes bioactivity measurements
5. records rejected data and rejection reasons
6. resolves unique ChEMBL compounds
7. enriches compounds through PubChem in batches
8. checkpoints enrichment results
9. performs duplicate and conflict analysis
10. generates a quality report
11. initializes the PostgreSQL catalog
12. loads compounds, targets, assays, activities, and provenance

## Testing

Run:

```bash
python -m pytest
python -m ruff check .
```

The test suite covers:

- ChEMBL API client behavior
- PubChem API client behavior
- provenance and checksums
- raw-data storage
- normalization
- rejection handling
- compound enrichment
- batch enrichment
- PostgreSQL schema loading
- catalog loaders
- duplicate/conflict detection
- quality reporting
- CLI argument parsing

## Example SQL Queries

Example queries are available in:

```text
sql/example_queries.sql
```

### Most Potent EGFR IC50 Measurements

Activity values should only be ranked when the measurement type and units are comparable.

For example, IC50 and Ki are different pharmacological measurements and should not be mixed into a single numeric ranking merely because both are reported in nM.

```sql
SELECT
    c.molecule_chembl_id,
    c.pubchem_cid,
    c.molecular_formula,
    a.activity_type,
    a.activity_value,
    a.activity_units,
    ass.assay_chembl_id
FROM activities AS a
JOIN compounds AS c
    ON c.compound_id = a.compound_id
JOIN targets AS t
    ON t.target_id = a.target_id
LEFT JOIN assays AS ass
    ON ass.assay_id = a.assay_id
WHERE t.target_chembl_id = 'CHEMBL203'
  AND a.activity_type = 'IC50'
  AND a.activity_units = 'nM'
ORDER BY a.activity_value ASC
LIMIT 20;
```

Other included examples show:

- activity counts by measurement type
- compounds measured across multiple assays
- source and ingestion provenance
- lineage from activity rows back to source ingestion runs

## Reproducibility

The catalog is designed so that pipeline executions can be traced through:

```text
source
  -> ingestion run
      -> raw file
          -> checksum
              -> normalized records
                  -> compound enrichment
                      -> PostgreSQL catalog
```

Load operations are designed to be idempotent so the same dataset can be processed repeatedly without duplicating core catalog entities.

External enrichment results are checkpointed so completed work can be reused after interrupted runs.

## Project Structure

```text
drug-discovery-data-catalog/
├── data/
│   ├── cache/
│   ├── raw/
│   └── curated/
├── sql/
│   └── example_queries.sql
├── src/
│   └── drug_catalog/
│       ├── clients/
│       │   ├── chembl.py
│       │   └── pubchem.py
│       ├── batch_enrichment.py
│       ├── cache.py
│       ├── cli.py
│       ├── compound_storage.py
│       ├── conflicts.py
│       ├── database.py
│       ├── enrichment.py
│       ├── loaders.py
│       ├── models.py
│       ├── normalization.py
│       ├── provenance.py
│       ├── quality.py
│       ├── reporting.py
│       ├── schema.sql
│       └── storage.py
├── tests/
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Tech Stack

- Python 3.12
- PostgreSQL
- SQL
- Docker / Docker Compose
- ChEMBL REST API
- PubChem PUG REST API
- HTTPX
- Pydantic
- Psycopg
- Pytest
- Ruff
