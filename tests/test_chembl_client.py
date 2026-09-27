import httpx

from drug_catalog.clients.chembl import ChEMBLClient


def test_fetch_database_version(monkeypatch) -> None:
    payload = {
        "chembl_db_version": "ChEMBL_37",
        "chembl_release_date": "2026-05-01",
        "status": "UP",
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

    version = client.fetch_database_version()

    assert version == "ChEMBL_37"
