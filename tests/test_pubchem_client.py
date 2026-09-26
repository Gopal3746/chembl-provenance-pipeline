import httpx

from drug_catalog.clients.pubchem import PubChemClient


def test_fetch_compound_by_inchikey(monkeypatch) -> None:
    payload = {
        "PropertyTable": {
            "Properties": [
                {
                    "CID": 123,
                    "MolecularFormula": "C10H12N2",
                    "MolecularWeight": "160.22",
                    "SMILES": "CC1=CC=CC=C1",
                    "ConnectivitySMILES": "CC1=CC=CC=C1",
                    "InChI": "InChI=1S/example",
                    "InChIKey": "ABCDEFGHIJKLMN-ABCDEFGHIJ-A",
                    "IUPACName": "example compound",
                }
            ]
        }
    }

    def mock_get(self, url):
        request = httpx.Request("GET", url)

        return httpx.Response(
            status_code=200,
            json=payload,
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    client = PubChemClient()

    result = client.fetch_compound_by_inchikey(
        "ABCDEFGHIJKLMN-ABCDEFGHIJ-A"
    )

    assert result is not None
    assert result["CID"] == 123
    assert result["MolecularFormula"] == "C10H12N2"

def test_fetch_compound_by_inchikey_returns_none_for_404(
    monkeypatch,
) -> None:
    def mock_get(self, url):
        request = httpx.Request("GET", url)

        return httpx.Response(
            status_code=404,
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    client = PubChemClient()

    result = client.fetch_compound_by_inchikey(
        "DOESNOTEXIST"
    )

    assert result is None
