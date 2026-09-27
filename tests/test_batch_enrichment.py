from decimal import Decimal

from drug_catalog.batch_enrichment import (
    enrich_compounds,
    get_unique_compound_ids,
)
from drug_catalog.normalization import NormalizedActivity


def make_activity(
    molecule_chembl_id: str,
) -> NormalizedActivity:
    return NormalizedActivity(
        activity_id=1,
        molecule_chembl_id=molecule_chembl_id,
        target_chembl_id="CHEMBL203",
        assay_chembl_id=None,
        document_chembl_id=None,
        activity_type="IC50",
        activity_value=Decimal(10),
        activity_units="nM",
    )


def test_get_unique_compound_ids() -> None:
    activities = [
        make_activity("CHEMBL2"),
        make_activity("CHEMBL1"),
        make_activity("CHEMBL2"),
    ]

    result = get_unique_compound_ids(activities)

    assert result == [
        "CHEMBL1",
        "CHEMBL2",
    ]


def test_enrich_compounds() -> None:
    class FakeChEMBLClient:
        def fetch_molecules(self, molecule_chembl_ids):
            return {
                molecule_id: {
                    "molecule_chembl_id": molecule_id,
                    "molecule_structures": {
                        "standard_inchi_key": (
                            f"{molecule_id}-KEY"
                        )
                    },
                }
                for molecule_id in molecule_chembl_ids
            }

    class FakePubChemClient:
        def fetch_compounds_by_inchikeys(self, inchikeys):
            return {
                inchikey: {
                    "CID": 123,
                    "MolecularFormula": "C10H10",
                    "MolecularWeight": "130.19",
                    "SMILES": "CC",
                    "ConnectivitySMILES": "CC",
                    "InChI": "InChI=1S/example",
                    "InChIKey": inchikey,
                    "IUPACName": "example",
                }
                for inchikey in inchikeys
            }

    activities = [
        make_activity("CHEMBL1"),
        make_activity("CHEMBL1"),
    ]

    result = enrich_compounds(
        activities,
        chembl_client=FakeChEMBLClient(),
        pubchem_client=FakePubChemClient(),
    )

    assert len(result.compounds) == 1
    assert len(result.failures) == 0

    compound = result.compounds[0]

    assert compound.molecule_chembl_id == "CHEMBL1"
    assert compound.pubchem_cid == 123


def test_enrich_compounds_tracks_missing_inchikey() -> None:
    class FakeChEMBLClient:
        def fetch_molecules(self, molecule_chembl_ids):
            return {
                molecule_id: {
                    "molecule_chembl_id": molecule_id,
                    "molecule_structures": None,
                }
                for molecule_id in molecule_chembl_ids
            }

    class FakePubChemClient:
        def fetch_compounds_by_inchikeys(self, inchikeys):
            raise AssertionError(
                "PubChem should not be called"
            )

    activities = [
        make_activity("CHEMBL1"),
    ]

    result = enrich_compounds(
        activities,
        chembl_client=FakeChEMBLClient(),
        pubchem_client=FakePubChemClient(),
    )

    assert len(result.compounds) == 0
    assert len(result.failures) == 1

    assert result.failures[0].molecule_chembl_id == "CHEMBL1"
    assert result.failures[0].reason == "missing_inchikey"
