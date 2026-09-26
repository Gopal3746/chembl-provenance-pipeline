from decimal import Decimal

from drug_catalog.conflicts import analyze_activity_duplicates
from drug_catalog.normalization import NormalizedActivity


def make_activity(
    *,
    activity_id: int,
    molecule_chembl_id: str = "CHEMBL1",
    assay_chembl_id: str = "CHEMBL_A1",
    value: str = "10",
) -> NormalizedActivity:
    return NormalizedActivity(
        activity_id=activity_id,
        molecule_chembl_id=molecule_chembl_id,
        target_chembl_id="CHEMBL203",
        assay_chembl_id=assay_chembl_id,
        document_chembl_id=None,
        activity_type="IC50",
        activity_value=Decimal(value),
        activity_units="nM",
    )


def test_detects_exact_duplicate_group() -> None:
    activities = [
        make_activity(
            activity_id=1,
            value="10",
        ),
        make_activity(
            activity_id=2,
            value="10",
        ),
    ]

    result = analyze_activity_duplicates(activities)

    assert result.repeated_measurement_groups == 1
    assert result.exact_duplicate_groups == 1
    assert result.conflicting_measurement_groups == 0
    assert result.conflicts == []


def test_detects_conflicting_measurements() -> None:
    activities = [
        make_activity(
            activity_id=1,
            value="10",
        ),
        make_activity(
            activity_id=2,
            value="20",
        ),
    ]

    result = analyze_activity_duplicates(activities)

    assert result.repeated_measurement_groups == 1
    assert result.exact_duplicate_groups == 0
    assert result.conflicting_measurement_groups == 1

    conflict = result.conflicts[0]

    assert conflict.activity_ids == (1, 2)
    assert conflict.values == (
        Decimal(10),
        Decimal(20),
    )


def test_different_assays_are_not_grouped() -> None:
    activities = [
        make_activity(
            activity_id=1,
            assay_chembl_id="CHEMBL_A1",
            value="10",
        ),
        make_activity(
            activity_id=2,
            assay_chembl_id="CHEMBL_A2",
            value="20",
        ),
    ]

    result = analyze_activity_duplicates(activities)

    assert result.repeated_measurement_groups == 0
    assert result.exact_duplicate_groups == 0
    assert result.conflicting_measurement_groups == 0
