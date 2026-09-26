from __future__ import annotations

from dataclasses import dataclass

from drug_catalog.clients.chembl import ChEMBLClient
from drug_catalog.clients.pubchem import PubChemClient
from drug_catalog.enrichment import build_compound_record, extract_inchikey
from drug_catalog.models import CompoundRecord
from drug_catalog.normalization import NormalizedActivity


@dataclass(frozen=True)
class EnrichmentFailure:
    molecule_chembl_id: str
    reason: str


@dataclass(frozen=True)
class BatchEnrichmentResult:
    compounds: list[CompoundRecord]
    failures: list[EnrichmentFailure]


def get_unique_compound_ids(
    activities: list[NormalizedActivity],
) -> list[str]:
    return sorted(
        {
            activity.molecule_chembl_id
            for activity in activities
        }
    )


def enrich_compounds(
    activities: list[NormalizedActivity],
    *,
    chembl_client: ChEMBLClient,
    pubchem_client: PubChemClient,
) -> BatchEnrichmentResult:
    compounds: list[CompoundRecord] = []
    failures: list[EnrichmentFailure] = []

    molecule_ids = get_unique_compound_ids(activities)

    for molecule_chembl_id in molecule_ids:
        chembl_molecule = chembl_client.fetch_molecule(
            molecule_chembl_id
        )

        inchikey = extract_inchikey(chembl_molecule)

        if inchikey is None:
            failures.append(
                EnrichmentFailure(
                    molecule_chembl_id=molecule_chembl_id,
                    reason="missing_inchikey",
                )
            )
            continue

        pubchem_record = pubchem_client.fetch_compound_by_inchikey(
            inchikey
        )

        if pubchem_record is None:
            failures.append(
                EnrichmentFailure(
                    molecule_chembl_id=molecule_chembl_id,
                    reason="pubchem_not_found",
                )
            )
            continue

        compound = build_compound_record(
            molecule_chembl_id=molecule_chembl_id,
            inchikey=inchikey,
            pubchem_record=pubchem_record,
        )

        compounds.append(compound)

    return BatchEnrichmentResult(
        compounds=compounds,
        failures=failures,
    )
