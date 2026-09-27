from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

PUBCHEM_BASE_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
)

PUBCHEM_PROPERTIES = [
    "MolecularFormula",
    "MolecularWeight",
    "SMILES",
    "ConnectivitySMILES",
    "InChI",
    "InChIKey",
    "IUPACName",
]

DEFAULT_PUBCHEM_BATCH_SIZE = 50


class PubChemClient:
    def __init__(
        self,
        base_url: str = PUBCHEM_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_compound_by_inchikey(
        self,
        inchikey: str,
    ) -> dict[str, Any] | None:
        encoded_inchikey = quote(
            inchikey,
            safe="",
        )

        properties = ",".join(
            PUBCHEM_PROPERTIES
        )

        url = (
            f"{self.base_url}/compound/inchikey/"
            f"{encoded_inchikey}/property/"
            f"{properties}/JSON"
        )

        with httpx.Client(
            timeout=self.timeout
        ) as client:
            response = client.get(url)

            if response.status_code == 404:
                return None

            response.raise_for_status()

            payload = response.json()

        property_table = payload.get(
            "PropertyTable",
            {},
        )

        compounds = property_table.get(
            "Properties",
            [],
        )

        if not compounds:
            return None

        return compounds[0]

    def fetch_compounds_by_inchikeys(
        self,
        inchikeys: list[str],
        *,
        batch_size: int = DEFAULT_PUBCHEM_BATCH_SIZE,
    ) -> dict[str, dict[str, Any]]:
        compounds_by_key: dict[
            str,
            dict[str, Any],
        ] = {}

        if not inchikeys:
            return compounds_by_key

        properties = ",".join(
            PUBCHEM_PROPERTIES
        )

        with httpx.Client(
            timeout=self.timeout
        ) as client:
            for start in range(
                0,
                len(inchikeys),
                batch_size,
            ):
                batch = inchikeys[
                    start : start + batch_size
                ]

                identifiers = ",".join(batch)

                url = (
                    f"{self.base_url}/compound/inchikey/"
                    f"{identifiers}/property/"
                    f"{properties}/JSON"
                )

                response = client.get(url)

                if response.status_code == 404:
                    continue

                response.raise_for_status()

                payload = response.json()

                property_table = payload.get(
                    "PropertyTable",
                    {},
                )

                compounds = property_table.get(
                    "Properties",
                    [],
                )

                for compound in compounds:
                    inchikey = compound.get(
                        "InChIKey"
                    )

                    if inchikey:
                        compounds_by_key[
                            inchikey
                        ] = compound

        return compounds_by_key
