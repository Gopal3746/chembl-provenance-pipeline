from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from drug_catalog.models import IngestionRun, RawFileMetadata, SourceMetadata
from drug_catalog.provenance import calculate_sha256


def save_raw_records(
    records: list[dict[str, Any]],
    *,
    source_name: str,
    source_version: str | None,
    endpoint: str,
    query_parameters: dict[str, str],
    output_dir: str | Path,
    file_name: str,
    pipeline_version: str = "0.1.0",
) -> IngestionRun:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    raw_file_path = output_path / file_name

    with raw_file_path.open("w", encoding="utf-8") as file_handle:
        json.dump(
            records,
            file_handle,
            indent=2,
            sort_keys=True,
        )

    checksum = calculate_sha256(raw_file_path)

    retrieved_at = datetime.now(UTC)

    source_metadata = SourceMetadata(
        source_name=source_name,
        source_version=source_version,
        endpoint=endpoint,
        query_parameters=query_parameters,
        retrieved_at=retrieved_at,
    )

    raw_file_metadata = RawFileMetadata(
        file_path=str(raw_file_path),
        sha256=checksum,
        record_count=len(records),
    )

    run_id = (
        f"{source_name.lower()}-"
        f"{retrieved_at.strftime('%Y%m%dT%H%M%SZ')}"
    )

    ingestion_run = IngestionRun(
        run_id=run_id,
        source=source_metadata,
        raw_file=raw_file_metadata,
        pipeline_version=pipeline_version,
    )

    manifest_path = raw_file_path.with_suffix(".metadata.json")

    with manifest_path.open("w", encoding="utf-8") as file_handle:
        json.dump(
            ingestion_run.model_dump(mode="json"),
            file_handle,
            indent=2,
            sort_keys=True,
        )

    return ingestion_run
