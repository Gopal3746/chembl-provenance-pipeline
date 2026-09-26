from drug_catalog.enrichment import (
    build_compound_record,
    extract_inchikey,
)


def test_extract_inchikey() -> None:
    molecule = {
        "molecule_structures": {
            "standard_inchi_key": "ABCDEFGHIJKLMN-ABCDEFGHIJ-A"
        }
    }

    result = extract_inchikey(molecule)

    assert result == "ABCDEFGHIJKLMN-ABCDEFGHIJ-A"


def test_extract_inchikey_handles_missing_structure() -> None:
    result = extract_inchikey(
        {
            "molecule_structures": None,
        }
    )

    assert result is None


def test_build_compound_record() -> None:
    pubchem_record = {
        "CID": 123,
        "MolecularFormula": "C10H12N2",
        "MolecularWeight": "160.22",
        "SMILES": "CC1=CC=CC=C1",
        "ConnectivitySMILES": "CC1=CC=CC=C1",
        "InChI": "InChI=1S/example",
        "InChIKey": "ABCDEFGHIJKLMN-ABCDEFGHIJ-A",
        "IUPACName": "example compound",
    }

    result = build_compound_record(
        molecule_chembl_id="CHEMBL1",
        inchikey="ABCDEFGHIJKLMN-ABCDEFGHIJ-A",
        pubchem_record=pubchem_record,
    )

    assert result.molecule_chembl_id == "CHEMBL1"
    assert result.pubchem_cid == 123
    assert result.molecular_formula == "C10H12N2"
    assert result.molecular_weight == 160.22
