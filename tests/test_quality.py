from drug_catalog.normalization import (
    RejectedActivity,
    RejectionReason,
)
from drug_catalog.quality import build_quality_report


def test_build_quality_report() -> None:
    rejected = [
        RejectedActivity(
            record={"activity_id": 1},
            reason=RejectionReason.UNSUPPORTED_UNITS,
        ),
        RejectedActivity(
            record={"activity_id": 2},
            reason=RejectionReason.UNSUPPORTED_UNITS,
        ),
        RejectedActivity(
            record={"activity_id": 3},
            reason=RejectionReason.MISSING_OR_INVALID_VALUE,
        ),
    ]

    report = build_quality_report(
        total_records=10,
        normalized_records=7,
        rejected=rejected,
    )

    assert report.total_records == 10
    assert report.normalized_records == 7
    assert report.rejected_records == 3

    assert report.rejection_reasons == {
        "unsupported_units": 2,
        "missing_or_invalid_value": 1,
    }
