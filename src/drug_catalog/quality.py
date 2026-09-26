from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from drug_catalog.normalization import RejectedActivity


@dataclass(frozen=True)
class DataQualityReport:
    total_records: int
    normalized_records: int
    rejected_records: int
    rejection_reasons: dict[str, int]


def build_quality_report(
    total_records: int,
    normalized_records: int,
    rejected: list[RejectedActivity],
) -> DataQualityReport:
    counts = Counter(item.reason.value for item in rejected)

    return DataQualityReport(
        total_records=total_records,
        normalized_records=normalized_records,
        rejected_records=len(rejected),
        rejection_reasons=dict(counts),
    )
