from __future__ import annotations

from typing import Any

import httpx

CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

DEFAULT_PAGE_SIZE = 100
DEFAULT_MOLECULE_BATCH_SIZE = 50


class ChEMBLClient:
    def __init__(
        self,
        base_url: str = CHEMBL_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_status(self) -> dict[str, Any]:
        url = f"{self.base_url}/status.json"

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url)
            response.raise_for_status()

            return response.json()

    def fetch_database_version(self) -> str | None:
        status = self.fetch_status()

        version = status.get("chembl_db_version")

        if version is None:
            return None

        return str(version)

    def fetch_molecule(
        self,
        molecule_chembl_id: str,
    ) -> dict[str, Any]:
        url = (
            f"{self.base_url}/molecule/"
            f"{molecule_chembl_id}.json"
        )

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url)
            response.raise_for_status()

            return response.json()

    def fetch_molecules(
        self,
        molecule_chembl_ids: list[str],
        *,
        batch_size: int = DEFAULT_MOLECULE_BATCH_SIZE,
    ) -> dict[str, dict[str, Any]]:
        molecules: dict[str, dict[str, Any]] = {}

        if not molecule_chembl_ids:
            return molecules

        url = f"{self.base_url}/molecule.json"

        with httpx.Client(timeout=self.timeout) as client:
            for start in range(
                0,
                len(molecule_chembl_ids),
                batch_size,
            ):
                batch = molecule_chembl_ids[
                    start : start + batch_size
                ]

                params = {
                    "molecule_chembl_id__in": ",".join(batch),
                    "limit": batch_size,
                }

                response = client.get(
                    url,
                    params=params,
                )
                response.raise_for_status()

                payload = response.json()

                for molecule in payload.get(
                    "molecules",
                    [],
                ):
                    molecule_id = molecule.get(
                        "molecule_chembl_id"
                    )

                    if molecule_id:
                        molecules[molecule_id] = molecule

        return molecules

    def fetch_activities(
        self,
        target_chembl_id: str,
        limit: int = DEFAULT_PAGE_SIZE,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        activities: list[dict[str, Any]] = []

        url = f"{self.base_url}/activity.json"

        params: dict[str, str | int] | None = {
            "target_chembl_id": target_chembl_id,
            "limit": limit,
            "offset": 0,
        }

        with httpx.Client(timeout=self.timeout) as client:
            while url is not None:
                response = client.get(
                    url,
                    params=params,
                )
                response.raise_for_status()

                payload = response.json()

                page_activities = payload.get(
                    "activities",
                    [],
                )

                activities.extend(page_activities)

                if (
                    max_records is not None
                    and len(activities) >= max_records
                ):
                    return activities[:max_records]

                page_meta = payload.get(
                    "page_meta",
                    {},
                )

                next_page = page_meta.get("next")

                if not next_page:
                    break

                if next_page.startswith("http"):
                    url = next_page
                else:
                    url = (
                        "https://www.ebi.ac.uk"
                        f"{next_page}"
                    )

                params = None

        return activities
