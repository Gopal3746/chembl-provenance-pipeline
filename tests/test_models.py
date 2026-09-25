from datetime import UTC, datetime

from drug_catalog.models import IngestionRun, RawFileMetadata, SourceMetadata


def test_ingestion_run_model() -> None:
    source = SourceMetadata(
        source_name="ChEMBL",
        source_version="example-version",
        endpoint="https://www.ebi.ac.uk/chembl/api/data/activity.json",
        query_parameters={"target_chembl_id": "CHEMBL203"},
        retrieved_at=datetime.now(UTC),
    )

    raw_file = RawFileMetadata(
        file_path="data/raw/chembl/activity.json",
        sha256="abc123",
        record_count=100,
    )

    run = IngestionRun(
        run_id="run-001",
        source=source,
        raw_file=raw_file,
        pipeline_version="0.1.0",
    )

    assert run.source.source_name == "ChEMBL"
    assert run.raw_file.record_count == 100
    assert run.pipeline_version == "0.1.0"
