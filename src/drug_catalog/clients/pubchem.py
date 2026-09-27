from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from drug_catalog.cache import JsonRecordCache

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

DEFAULT_PUBCHEM_BATCH_SIZE = 20
DEFAULT_MAX_RETRIES = 4
DEFAULT_RETRY_DELAY = 2.0


class PubChemClient:
    def __init__(
        self,
        base_url: str = PUBCHEM_BASE_URL,
        timeout: float = 60.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _get_with_retry(
        self,
        client: httpx.Client,
        url: str,
    ) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(
            1,
            self.max_retries + 1,
        ):
            try:
                response = client.get(url)

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    if attempt == self.max_retries:
                        response.raise_for_status()

                    delay = (
                        self.retry_delay
                        * (2 ** (attempt - 1))
                    )

                    print(
                        "PubChem temporarily unavailable "
                        f"(HTTP {response.status_code}). "
                        f"Retrying in {delay:.0f}s..."
                    )

                    time.sleep(delay)
                    continue

                return response

            except httpx.TimeoutException as exc:
                last_error = exc

                if attempt == self.max_retries:
                    raise

                delay = (
                    self.retry_delay
                    * (2 ** (attempt - 1))
                )

                print(
                    "PubChem request timed out. "
                    f"Retrying in {delay:.0f}s..."
                )

                time.sleep(delay)

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "PubChem request failed unexpectedly."
        )

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
            response = self._get_with_retry(
                client,
                url,
            )

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
        cache_path: str | Path = (
            "data/cache/pubchem_compounds.json"
        ),
    ) -> dict[str, dict[str, Any]]:
        cache = JsonRecordCache(cache_path)

        compounds_by_key: dict[
            str,
            dict[str, Any],
        ] = {}

        if not inchikeys:
            return compounds_by_key

        cached_count = 0
        missing_inchikeys: list[str] = []

        for inchikey in inchikeys:
            cached = cache.get(inchikey)

            if cached is not None:
                compounds_by_key[inchikey] = cached
                cached_count += 1
            else:
                missing_inchikeys.append(inchikey)

        print(
            f"PubChem cache: {cached_count} hits, "
            f"{len(missing_inchikeys)} remaining."
        )

        if not missing_inchikeys:
            return compounds_by_key

        properties = ",".join(
            PUBCHEM_PROPERTIES
        )

        total_batches = (
            len(missing_inchikeys)
            + batch_size
            - 1
        ) // batch_size

        with httpx.Client(
            timeout=self.timeout
        ) as client:
            for batch_number, start in enumerate(
                range(
                    0,
                    len(missing_inchikeys),
                    batch_size,
                ),
                start=1,
            ):
                batch = missing_inchikeys[
                    start : start + batch_size
                ]

                identifiers = ",".join(batch)

                url = (
                    f"{self.base_url}/compound/inchikey/"
                    f"{identifiers}/property/"
                    f"{properties}/JSON"
                )

                print(
                    "PubChem batch "
                    f"{batch_number}/{total_batches} "
                    f"({len(batch)} compounds)..."
                )

                response = self._get_with_retry(
                    client,
                    url,
                )

                if response.status_code == 404:
                    print(
                        "Batch lookup returned 404; "
                        "checking compounds individually..."
                    )

                    for inchikey in batch:
                        compound = (
                            self.fetch_compound_by_inchikey(
                                inchikey
                            )
                        )

                        if compound is None:
                            continue

                        compounds_by_key[
                            inchikey
                        ] = compound

                        cache.set(
                            inchikey,
                            compound,
                        )

                    cache.save()
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

                    if not inchikey:
                        continue

                    compounds_by_key[
                        inchikey
                    ] = compound

                    cache.set(
                        inchikey,
                        compound,
                    )

                # Persist every successful batch so a
                # later failure does not lose prior work.
                cache.save()

        return compounds_by_key
