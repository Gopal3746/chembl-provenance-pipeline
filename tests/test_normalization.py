from decimal import Decimal

from drug_catalog.normalization import (
    RejectionReason,
    normalize_activities,
    normalize_activity,
)


def test_normalize_activity() -> None:
    record = {
        "activity_id": 123,
        "molecule_chembl_id": "CHEMBL1",
        "target_chembl_id": "CHEMBL203",
        "assay_chembl_id": "CHEMBL_A1",
        "document_chembl_id": "CHEMBL_DOC1",
        "standard_type": "IC50",
        "standard_value": "12.5",
        "standard_units": "nM",
        "standard_relation": "=",
        "pchembl_value": "7.9",
    }

    result, reason = normalize_activity(record)

    assert result is not None
    assert reason is None

    assert result.activity_id == 123
    assert result.molecule_chembl_id == "CHEMBL1"
    assert result.activity_type == "IC50"
    assert result.activity_value == Decimal("12.5")
    assert result.activity_units == "nM"
    assert result.pchembl_value == Decimal("7.9")


def test_normalize_activity_rejects_missing_value() -> None:
    record = {
        "activity_id": 123,
        "molecule_chembl_id": "CHEMBL1",
        "target_chembl_id": "CHEMBL203",
        "standard_type": "IC50",
        "standard_value": None,
        "standard_units": "nM",
    }

    result, reason = normalize_activity(record)

    assert result is None
    assert reason == RejectionReason.MISSING_OR_INVALID_VALUE


def test_normalize_activity_rejects_unsupported_units() -> None:
    record = {
        "activity_id": 123,
        "molecule_chembl_id": "CHEMBL1",
        "target_chembl_id": "CHEMBL203",
        "standard_type": "IC50",
        "standard_value": "10",
        "standard_units": "uM",
    }

    result, reason = normalize_activity(record)

    assert result is None
    assert reason == RejectionReason.UNSUPPORTED_UNITS


def test_normalize_activities_counts_rejections() -> None:
    records = [
        {
            "activity_id": 1,
            "molecule_chembl_id": "CHEMBL1",
            "target_chembl_id": "CHEMBL203",
            "standard_type": "IC50",
            "standard_value": "10",
            "standard_units": "nM",
        },
        {
            "activity_id": 2,
            "molecule_chembl_id": "CHEMBL2",
            "target_chembl_id": "CHEMBL203",
            "standard_type": "IC50",
            "standard_value": None,
            "standard_units": "nM",
        },
    ]

    normalized, rejected = normalize_activities(records)

    assert len(normalized) == 1
    assert len(rejected) == 1
    assert rejected[0].reason == RejectionReason.MISSING_OR_INVALID_VALUE
