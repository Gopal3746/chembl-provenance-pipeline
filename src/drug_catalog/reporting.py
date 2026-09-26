from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from drug_catalog.batch_enrichment import BatchEnrichmentResult
from drug_catalog.conflicts import DuplicateSummary
from drug_catalog.normalization import RejectedActivity
from drug_catalog.quality import build_quality_report


@dataclass(frozen=True)
class CatalogQualityReport:
    raw_activity_records: int
    normalized_activity_records: int
    rejected_activity_records: int
    rejection_reasons: dict[str, int]

    unique_compounds: int
    enriched_compounds: int
    enrichment_failures: int

    repeated_measurement_groups: int
    exact_duplicate_groups: int
    conflicting_measurement_groups: int


def build_catalog_quality_report(
    *,
    raw_activity_count: int,
    normalized_activity_count: int,
    rejected: list[RejectedActivity],
    unique_compound_count: int,
    enrichment_result: BatchEnrichmentResult,
    duplicate_summary: DuplicateSummary,
) -> CatalogQualityReport:
    activity_quality = build_quality_report(
        total_records=raw_activity_count,
        normalized_records=normalized_activity_count,
        rejected=rejected,
    )

    return CatalogQualityReport(
        raw_activity_records=activity_quality.total_records,
        normalized_activity_records=activity_quality.normalized_records,
        rejected_activity_records=activity_quality.rejected_records,
        rejection_reasons=activity_quality.rejection_reasons,
        unique_compounds=unique_compound_count,
        enriched_compounds=len(enrichment_result.compounds),
        enrichment_failures=len(enrichment_result.failures),
        repeated_measurement_groups=(
            duplicate_summary.repeated_measurement_groups
        ),
        exact_duplicate_groups=(
            duplicate_summary.exact_duplicate_groups
        ),
        conflicting_measurement_groups=(
            duplicate_summary.conflicting_measurement_groups
        ),
    )


def save_catalog_quality_report(
    report: CatalogQualityReport,
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(
            asdict(report),
            file_handle,
            indent=2,
            sort_keys=True,
        )
