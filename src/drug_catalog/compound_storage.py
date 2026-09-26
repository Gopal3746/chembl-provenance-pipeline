from __future__ import annotations

from pathlib import Path

from drug_catalog.models import CompoundRecord, IngestionRun
from drug_catalog.storage import save_raw_records


def save_enriched_compounds(
    compounds: list[CompoundRecord],
    *,
    output_dir: str | Path,
    file_name: str = "pubchem_compounds.json",
    pipeline_version: str = "0.1.0",
) -> IngestionRun:
    records = [
        compound.model_dump(mode="json")
        for compound in compounds
    ]

    return save_raw_records(
        records,
        source_name="PubChem",
        source_version=None,
        endpoint="https://pubchem.ncbi.nlm.nih.gov/rest/pug",
        query_parameters={
            "lookup": "InChIKey",
            "properties": (
                "MolecularFormula,MolecularWeight,SMILES,"
                "ConnectivitySMILES,InChI,InChIKey,IUPACName"
            ),
        },
        output_dir=output_dir,
        file_name=file_name,
        pipeline_version=pipeline_version,
    )
