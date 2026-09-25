from __future__ import annotations

from typing import Any

import httpx

CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

DEFAULT_PAGE_SIZE = 100


class ChEMBLClient:
    def __init__(
        self,
        base_url: str = CHEMBL_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

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
                response = client.get(url, params=params)
                response.raise_for_status()

                payload = response.json()

                page_activities = payload.get("activities", [])
                activities.extend(page_activities)

                if max_records is not None and len(activities) >= max_records:
                    return activities[:max_records]

                page_meta = payload.get("page_meta", {})
                next_page = page_meta.get("next")

                if not next_page:
                    break

                if next_page.startswith("http"):
                    url = next_page
                else:
                    url = f"https://www.ebi.ac.uk{next_page}"

                # The next URL already contains pagination/query parameters.
                params = None

        return activities
