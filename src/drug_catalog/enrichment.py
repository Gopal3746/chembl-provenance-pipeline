from __future__ import annotations

from typing import Any

from drug_catalog.models import CompoundRecord


def extract_inchikey(
    chembl_molecule: dict[str, Any],
) -> str | None:
    structures = chembl_molecule.get("molecule_structures")

    if not structures:
        return None

    return structures.get("standard_inchi_key")


def build_compound_record(
    molecule_chembl_id: str,
    inchikey: str,
    pubchem_record: dict[str, Any],
) -> CompoundRecord:
    return CompoundRecord(
        molecule_chembl_id=molecule_chembl_id,
        pubchem_cid=pubchem_record.get("CID"),
        molecular_formula=pubchem_record.get("MolecularFormula"),
        molecular_weight=_parse_float(
            pubchem_record.get("MolecularWeight")
        ),
        smiles=pubchem_record.get("SMILES"),
        connectivity_smiles=pubchem_record.get(
            "ConnectivitySMILES"
        ),
        inchi=pubchem_record.get("InChI"),
        inchikey=inchikey,
        iupac_name=pubchem_record.get("IUPACName"),
    )


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
