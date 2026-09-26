from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel

SUPPORTED_ACTIVITY_TYPES = {
    "IC50",
    "Ki",
    "Kd",
    "EC50",
}

SUPPORTED_UNITS = {
    "nM",
}


class NormalizedActivity(BaseModel):
    activity_id: int | None
    molecule_chembl_id: str
    target_chembl_id: str
    assay_chembl_id: str | None
    document_chembl_id: str | None

    activity_type: str
    activity_value: Decimal
    activity_units: str

    relation: str | None = None
    pchembl_value: Decimal | None = None


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def normalize_activity(
    record: dict[str, Any],
) -> NormalizedActivity | None:
    molecule_chembl_id = record.get("molecule_chembl_id")
    target_chembl_id = record.get("target_chembl_id")
    activity_type = record.get("standard_type")
    activity_units = record.get("standard_units")

    activity_value = _parse_decimal(
        record.get("standard_value")
    )

    if not molecule_chembl_id:
        return None

    if not target_chembl_id:
        return None

    if activity_type not in SUPPORTED_ACTIVITY_TYPES:
        return None

    if activity_units not in SUPPORTED_UNITS:
        return None

    if activity_value is None:
        return None

    pchembl_value = _parse_decimal(
        record.get("pchembl_value")
    )

    return NormalizedActivity(
        activity_id=record.get("activity_id"),
        molecule_chembl_id=molecule_chembl_id,
        target_chembl_id=target_chembl_id,
        assay_chembl_id=record.get("assay_chembl_id"),
        document_chembl_id=record.get("document_chembl_id"),
        activity_type=activity_type,
        activity_value=activity_value,
        activity_units=activity_units,
        relation=record.get("standard_relation"),
        pchembl_value=pchembl_value,
    )


def normalize_activities(
    records: list[dict[str, Any]],
) -> tuple[list[NormalizedActivity], int]:
    normalized: list[NormalizedActivity] = []
    rejected = 0

    for record in records:
        activity = normalize_activity(record)

        if activity is None:
            rejected += 1
            continue

        normalized.append(activity)

    return normalized, rejected
