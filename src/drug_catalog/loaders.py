from __future__ import annotations

import json

from psycopg import Connection

from drug_catalog.models import CompoundRecord, IngestionRun
from drug_catalog.normalization import NormalizedActivity


def load_source(
    connection: Connection,
    run: IngestionRun,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO sources (
                source_name,
                source_version,
                endpoint
            )
            VALUES (%s, %s, %s)
            RETURNING source_id
            """,
            (
                run.source.source_name,
                run.source.source_version,
                run.source.endpoint,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Failed to insert source")

    return row[0]


def load_ingestion_run(
    connection: Connection,
    run: IngestionRun,
    source_id: int,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ingestion_runs (
                run_id,
                source_id,
                retrieved_at,
                query_parameters,
                raw_file_path,
                raw_file_sha256,
                record_count,
                pipeline_version
            )
            VALUES (
                %s, %s, %s, %s::jsonb,
                %s, %s, %s, %s
            )
            ON CONFLICT (run_id) DO NOTHING
            """,
            (
                run.run_id,
                source_id,
                run.source.retrieved_at,
                json.dumps(run.source.query_parameters),
                run.raw_file.file_path,
                run.raw_file.sha256,
                run.raw_file.record_count,
                run.pipeline_version,
            ),
        )


def load_compounds(
    connection: Connection,
    compounds: list[CompoundRecord],
) -> dict[str, int]:
    compound_ids: dict[str, int] = {}

    with connection.cursor() as cursor:
        for compound in compounds:
            cursor.execute(
                """
                INSERT INTO compounds (
                    molecule_chembl_id,
                    pubchem_cid,
                    molecular_formula,
                    molecular_weight,
                    smiles,
                    connectivity_smiles,
                    inchi,
                    inchikey,
                    iupac_name
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (molecule_chembl_id)
                DO UPDATE SET
                    pubchem_cid = EXCLUDED.pubchem_cid,
                    molecular_formula = EXCLUDED.molecular_formula,
                    molecular_weight = EXCLUDED.molecular_weight,
                    smiles = EXCLUDED.smiles,
                    connectivity_smiles = EXCLUDED.connectivity_smiles,
                    inchi = EXCLUDED.inchi,
                    inchikey = EXCLUDED.inchikey,
                    iupac_name = EXCLUDED.iupac_name,
                    updated_at = NOW()
                RETURNING compound_id
                """,
                (
                    compound.molecule_chembl_id,
                    compound.pubchem_cid,
                    compound.molecular_formula,
                    compound.molecular_weight,
                    compound.smiles,
                    compound.connectivity_smiles,
                    compound.inchi,
                    compound.inchikey,
                    compound.iupac_name,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    f"Failed to load {compound.molecule_chembl_id}"
                )

            compound_ids[compound.molecule_chembl_id] = row[0]

    return compound_ids


def load_target(
    connection: Connection,
    target_chembl_id: str,
    preferred_name: str | None = None,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO targets (
                target_chembl_id,
                preferred_name
            )
            VALUES (%s, %s)
            ON CONFLICT (target_chembl_id)
            DO UPDATE SET
                preferred_name = EXCLUDED.preferred_name
            RETURNING target_id
            """,
            (
                target_chembl_id,
                preferred_name,
            ),
        )

        row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Failed to load target")

    return row[0]


def load_activities(
    connection: Connection,
    activities: list[NormalizedActivity],
    *,
    compound_ids: dict[str, int],
    target_id: int,
    ingestion_run_id: str,
) -> int:
    inserted = 0

    with connection.cursor() as cursor:
        for activity in activities:
            if activity.activity_id is None:
                continue

            compound_id = compound_ids.get(
                activity.molecule_chembl_id
            )

            if compound_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO activities (
                    activity_id,
                    compound_id,
                    target_id,
                    document_chembl_id,
                    activity_type,
                    activity_value,
                    activity_units,
                    relation,
                    pchembl_value,
                    ingestion_run_id
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (activity_id) DO NOTHING
                RETURNING activity_id
                """,
                (
                    activity.activity_id,
                    compound_id,
                    target_id,
                    activity.document_chembl_id,
                    activity.activity_type,
                    activity.activity_value,
                    activity.activity_units,
                    activity.relation,
                    activity.pchembl_value,
                    ingestion_run_id,
                ),
            )

            if cursor.fetchone() is not None:
                inserted += 1

    return inserted
