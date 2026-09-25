from __future__ import annotations

import httpx

from drug_catalog.clients.chembl import ChEMBLClient


def test_fetch_activities_single_page(monkeypatch) -> None:
    payload = {
        "activities": [
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
                "standard_type": "Ki",
                "standard_value": "25",
                "standard_units": "nM",
            },
        ],
        "page_meta": {
            "next": None,
            "previous": None,
            "total_count": 2,
        },
    }

    def mock_get(self, url, params=None):
        request = httpx.Request("GET", url)

        return httpx.Response(
            status_code=200,
            json=payload,
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    client = ChEMBLClient()

    activities = client.fetch_activities(
        target_chembl_id="CHEMBL203",
    )

    assert len(activities) == 2
    assert activities[0]["molecule_chembl_id"] == "CHEMBL1"
    assert activities[0]["standard_type"] == "IC50"
    def test_fetch_activities_follows_pagination(monkeypatch) -> None:
        first_page = {
            "activities": [
                {
                    "activity_id": 1,
                    "molecule_chembl_id": "CHEMBL1",
                }
            ],
            "page_meta": {
                "next": "/chembl/api/data/activity.json?limit=1&offset=1",
            },
        }

        second_page = {
            "activities": [
                {
                    "activity_id": 2,
                    "molecule_chembl_id": "CHEMBL2",
                }
            ],
            "page_meta": {
                "next": None,
            },
        }

        call_count = 0

        def mock_get(self, url, params=None):
            nonlocal call_count

            call_count += 1

            payload = first_page if call_count == 1 else second_page

            request = httpx.Request("GET", url)

            return httpx.Response(
                status_code=200,
                json=payload,
                request=request,
            )

        monkeypatch.setattr(httpx.Client, "get", mock_get)

        client = ChEMBLClient()

        activities = client.fetch_activities(
            target_chembl_id="CHEMBL203",
            limit=1,
        )

        assert len(activities) == 2
        assert activities[0]["molecule_chembl_id"] == "CHEMBL1"
        assert activities[1]["molecule_chembl_id"] == "CHEMBL2"
        assert call_count == 2
        def test_fetch_activities_respects_max_records(monkeypatch) -> None:
            payload = {
                "activities": [
                    {"activity_id": 1},
                    {"activity_id": 2},
                    {"activity_id": 3},
                ],
                "page_meta": {
                    "next": None,
                },
            }

            def mock_get(self, url, params=None):
                request = httpx.Request("GET", url)

                return httpx.Response(
                    status_code=200,
                    json=payload,
                    request=request,
                )

            monkeypatch.setattr(httpx.Client, "get", mock_get)

            client = ChEMBLClient()

            activities = client.fetch_activities(
                target_chembl_id="CHEMBL203",
                max_records=2,
            )

            assert len(activities) == 2
