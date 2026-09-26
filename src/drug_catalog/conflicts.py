from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from drug_catalog.normalization import NormalizedActivity


@dataclass(frozen=True)
class ActivityGroupKey:
    molecule_chembl_id: str
    target_chembl_id: str
    assay_chembl_id: str | None
    activity_type: str
    activity_units: str


@dataclass(frozen=True)
class ActivityConflict:
    key: ActivityGroupKey
    activity_ids: tuple[int | None, ...]
    values: tuple[Decimal, ...]


@dataclass(frozen=True)
class DuplicateSummary:
    exact_duplicate_groups: int
    repeated_measurement_groups: int
    conflicting_measurement_groups: int
    conflicts: list[ActivityConflict]


def _group_key(
    activity: NormalizedActivity,
) -> ActivityGroupKey:
    return ActivityGroupKey(
        molecule_chembl_id=activity.molecule_chembl_id,
        target_chembl_id=activity.target_chembl_id,
        assay_chembl_id=activity.assay_chembl_id,
        activity_type=activity.activity_type,
        activity_units=activity.activity_units,
    )


def analyze_activity_duplicates(
    activities: list[NormalizedActivity],
) -> DuplicateSummary:
    grouped: dict[
        ActivityGroupKey,
        list[NormalizedActivity],
    ] = defaultdict(list)

    for activity in activities:
        grouped[_group_key(activity)].append(activity)

    exact_duplicate_groups = 0
    repeated_measurement_groups = 0
    conflicting_measurement_groups = 0
    conflicts: list[ActivityConflict] = []

    for key, group in grouped.items():
        if len(group) < 2:
            continue

        repeated_measurement_groups += 1

        values = {
            activity.activity_value
            for activity in group
        }

        if len(values) == 1:
            exact_duplicate_groups += 1
            continue

        conflicting_measurement_groups += 1

        conflicts.append(
            ActivityConflict(
                key=key,
                activity_ids=tuple(
                    activity.activity_id
                    for activity in group
                ),
                values=tuple(
                    activity.activity_value
                    for activity in group
                ),
            )
        )

    return DuplicateSummary(
        exact_duplicate_groups=exact_duplicate_groups,
        repeated_measurement_groups=repeated_measurement_groups,
        conflicting_measurement_groups=conflicting_measurement_groups,
        conflicts=conflicts,
    )
