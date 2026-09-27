# Drug Discovery Data Catalog

A reproducible scientific data engineering pipeline for ingesting, standardizing, enriching, validating, and cataloging compound-target bioactivity data with end-to-end provenance.

The project integrates public drug discovery data from ChEMBL and PubChem, preserves raw source records, performs quality checks, and loads curated scientific data into PostgreSQL for discovery and analysis.

## Why This Project Exists

Drug discovery datasets often come from heterogeneous scientific sources with different identifiers, schemas, completeness levels, and metadata conventions.

This project demonstrates a workflow for:

- integrating scientific datasets from multiple sources
- preserving raw source data
- standardizing bioactivity records
- enriching compounds across databases
- tracking data provenance and checksums
- identifying invalid or conflicting measurements
- cataloging curated records in PostgreSQL
- supporting reproducible SQL-based data discovery

## Data Sources

### ChEMBL

ChEMBL is used for:

- compound-target bioactivity records
- molecule identifiers
- assay identifiers
- document identifiers
- activity types such as IC50 and Ki
- standardized activity values

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

Compounds are linked across the two sources using InChIKey.

## Example Target

The current example pipeline uses:

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
raw activity JSON
    |
    +--> SHA-256 checksum
    +--> provenance manifest
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
ChEMBL molecule lookup
    |
    v
InChIKey
    |
    v
PubChem enrichment
    |
    +--> enriched compound JSON
    +--> provenance manifest
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

## Current Sample Results

For a 25-record ChEMBL sample targeting EGFR:

```text
Raw activity records:          25
Normalized activity records:   23
Rejected activity records:      2

Unique compounds:              13
PubChem compounds enriched:    13
Enrichment failures:            0

Assays cataloged:               6
Activities loaded:             23

Repeated measurement groups:    0
Exact duplicate groups:         0
Conflicting measurement groups: 0
```

Both rejected records were Ki measurements with missing activity values.

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
  "run_id": "chembl-20260925T215916Z",
  "source": {
    "source_name": "ChEMBL",
    "endpoint": "https://www.ebi.ac.uk/chembl/api/data/activity.json",
    "query_parameters": {
      "target_chembl_id": "CHEMBL203"
    }
  },
  "raw_file": {
    "record_count": 25,
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

The pipeline also detects repeated measurements and conflicting activity values for the same compound, target, assay, activity type, and units.

A consolidated report is generated at:

```text
data/curated/CHEMBL203_quality_report.json
```

Example:

```json
{
  "raw_activity_records": 25,
  "normalized_activity_records": 23,
  "rejected_activity_records": 2,
  "rejection_reasons": {
    "missing_or_invalid_value": 2
  },
  "unique_compounds": 13,
  "enriched_compounds": 13,
  "enrichment_failures": 0,
  "repeated_measurement_groups": 0,
  "exact_duplicate_groups": 0,
  "conflicting_measurement_groups": 0
}
```

## PostgreSQL Catalog

The relational catalog contains:

### `sources`

Scientific source systems such as ChEMBL and PubChem.

### `ingestion_runs`

Tracks individual source retrievals, query metadata, raw-file checksums, record counts, and pipeline versions.

### `compounds`

Cross-source compound metadata including ChEMBL identifiers, PubChem IDs, molecular properties, SMILES, and InChIKey.

### `targets`

Drug targets represented by ChEMBL target identifiers.

### `assays`

ChEMBL assay identifiers associated with targets.

### `activities`

Normalized compound-target bioactivity measurements linked to compounds, targets, assays, and source ingestion runs.

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

Install:

```bash
pip install -e ".[dev]"
```

Start PostgreSQL:

```bash
docker compose up -d
```

## Run the Pipeline

Run the complete pipeline for EGFR:

```bash
drug-catalog run \
  --target CHEMBL203 \
  --max-records 25
```

The command:

1. retrieves ChEMBL activity data
2. preserves raw records and provenance
3. normalizes activity measurements
4. enriches compounds through PubChem
5. performs data-quality checks
6. generates the quality report
7. initializes PostgreSQL
8. loads the curated catalog

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

Queries are available in:

```text
sql/example_queries.sql
```

Example — find the most potent measurements against EGFR:

```sql
SELECT
    c.molecule_chembl_id,
    c.pubchem_cid,
    c.molecular_formula,
    a.activity_type,
    a.activity_value,
    a.activity_units
FROM activities a
JOIN compounds c
    ON c.compound_id = a.compound_id
JOIN targets t
    ON t.target_id = a.target_id
WHERE t.target_chembl_id = 'CHEMBL203'
ORDER BY a.activity_value ASC
LIMIT 10;
```

Example results from the current sample include:

```text
CHEMBL69960    IC50       40 nM
CHEMBL68920    IC50       41 nM
CHEMBL76589    IC50      125 nM
CHEMBL69960    IC50      170 nM
CHEMBL68920    IC50      300 nM
```

## Reproducibility

The catalog is designed so that pipeline executions can be traced back to:

```text
source
  -> ingestion run
      -> raw file
          -> checksum
              -> normalized records
                  -> PostgreSQL catalog
```

Load operations are idempotent, allowing the same dataset to be processed multiple times without duplicating catalog entities.

## Project Structure

```text
drug-discovery-data-catalog/
├── data/
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
