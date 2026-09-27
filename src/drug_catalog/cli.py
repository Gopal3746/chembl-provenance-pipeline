from __future__ import annotations

import argparse

from drug_catalog.batch_enrichment import (
    enrich_compounds,
    get_unique_compound_ids,
)
from drug_catalog.clients.chembl import ChEMBLClient
from drug_catalog.clients.pubchem import PubChemClient
from drug_catalog.compound_storage import save_enriched_compounds
from drug_catalog.conflicts import analyze_activity_duplicates
from drug_catalog.database import connect, initialize_database
from drug_catalog.loaders import (
    load_activities,
    load_assays,
    load_compounds,
    load_ingestion_run,
    load_source,
    load_target,
)
from drug_catalog.normalization import normalize_activities
from drug_catalog.reporting import (
    build_catalog_quality_report,
    save_catalog_quality_report,
)
from drug_catalog.storage import save_raw_records


def run_pipeline(
    target_chembl_id: str,
    *,
    max_records: int | None = None,
) -> None:
    initialize_database()

    chembl_client = ChEMBLClient()
    pubchem_client = PubChemClient()

    chembl_version = chembl_client.fetch_database_version()

    print(
        f"Using ChEMBL release: "
        f"{chembl_version or 'unknown'}"
    )

    print(
        f"Fetching ChEMBL activities for "
        f"{target_chembl_id}..."
    )

    raw_activities = chembl_client.fetch_activities(
        target_chembl_id=target_chembl_id,
        max_records=max_records,
    )

    chembl_run = save_raw_records(
        raw_activities,
        source_name="ChEMBL",
        source_version=chembl_version,
        endpoint=(
            "https://www.ebi.ac.uk/chembl/api/data/"
            "activity.json"
        ),
        query_parameters={
            "target_chembl_id": target_chembl_id,
        },
        output_dir="data/raw/chembl",
        file_name=f"{target_chembl_id}_activities.json",
    )

    normalized, rejected = normalize_activities(
        raw_activities
    )

    unique_compound_ids = get_unique_compound_ids(
        normalized
    )

    print(
        f"Normalized {len(normalized)} activities "
        f"from {len(raw_activities)} raw records."
    )

    print(
        f"Enriching {len(unique_compound_ids)} "
        "unique compounds..."
    )

    enrichment_result = enrich_compounds(
        normalized,
        chembl_client=chembl_client,
        pubchem_client=pubchem_client,
    )

    pubchem_run = save_enriched_compounds(
        enrichment_result.compounds,
        output_dir="data/raw/pubchem",
        file_name=(
            f"{target_chembl_id}_pubchem_compounds.json"
        ),
    )

    duplicate_summary = analyze_activity_duplicates(
        normalized
    )

    quality_report = build_catalog_quality_report(
        raw_activity_count=len(raw_activities),
        normalized_activity_count=len(normalized),
        rejected=rejected,
        unique_compound_count=len(unique_compound_ids),
        enrichment_result=enrichment_result,
        duplicate_summary=duplicate_summary,
    )

    quality_report_path = (
        "data/curated/"
        f"{target_chembl_id}_quality_report.json"
    )

    save_catalog_quality_report(
        quality_report,
        quality_report_path,
    )

    with connect() as connection:
        chembl_source_id = load_source(
            connection,
            chembl_run,
        )

        load_ingestion_run(
            connection,
            chembl_run,
            chembl_source_id,
        )

        pubchem_source_id = load_source(
            connection,
            pubchem_run,
        )

        load_ingestion_run(
            connection,
            pubchem_run,
            pubchem_source_id,
        )

        compound_ids = load_compounds(
            connection,
            enrichment_result.compounds,
        )

        target_id = load_target(
            connection,
            target_chembl_id=target_chembl_id,
            preferred_name=None,
        )

        assay_ids = load_assays(
            connection,
            normalized,
            target_id=target_id,
        )

        loaded_activities = load_activities(
            connection,
            normalized,
            compound_ids=compound_ids,
            assay_ids=assay_ids,
            target_id=target_id,
            ingestion_run_id=chembl_run.run_id,
        )

        connection.commit()

    print()
    print("Pipeline complete.")
    print(
        f"ChEMBL release: "
        f"{chembl_version or 'unknown'}"
    )
    print(
        f"Raw activities: "
        f"{len(raw_activities)}"
    )
    print(
        f"Normalized activities: "
        f"{len(normalized)}"
    )
    print(
        f"Rejected activities: "
        f"{len(rejected)}"
    )
    print(
        f"Unique compounds: "
        f"{len(unique_compound_ids)}"
    )
    print(
        f"Enriched compounds: "
        f"{len(enrichment_result.compounds)}"
    )
    print(
        f"Enrichment failures: "
        f"{len(enrichment_result.failures)}"
    )
    print(
        f"Assays loaded: "
        f"{len(assay_ids)}"
    )
    print(
        f"Activities loaded: "
        f"{loaded_activities}"
    )
    print(
        f"Quality report: "
        f"{quality_report_path}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drug-catalog",
        description=(
            "Build a provenance-aware drug discovery "
            "data catalog."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run the data pipeline.",
    )

    run_parser.add_argument(
        "--target",
        required=True,
        help=(
            "ChEMBL target ID, "
            "for example CHEMBL203."
        ),
    )

    run_parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help=(
            "Optional maximum number "
            "of activity records."
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(
            args.target,
            max_records=args.max_records,
        )


if __name__ == "__main__":
    main()
