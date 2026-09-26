import json

from drug_catalog.compound_storage import save_enriched_compounds
from drug_catalog.models import CompoundRecord


def test_save_enriched_compounds(tmp_path) -> None:
    compounds = [
        CompoundRecord(
            molecule_chembl_id="CHEMBL1",
            pubchem_cid=123,
            molecular_formula="C10H12N2",
            molecular_weight=160.22,
            smiles="CC",
            connectivity_smiles="CC",
            inchi="InChI=1S/example",
            inchikey="ABCDEFGHIJKLMN-ABCDEFGHIJ-A",
            iupac_name="example compound",
        )
    ]

    run = save_enriched_compounds(
        compounds,
        output_dir=tmp_path,
    )

    raw_file = tmp_path / "pubchem_compounds.json"
    manifest_file = tmp_path / "pubchem_compounds.metadata.json"

    assert raw_file.exists()
    assert manifest_file.exists()

    saved_records = json.loads(raw_file.read_text())
    manifest = json.loads(manifest_file.read_text())

    assert len(saved_records) == 1
    assert saved_records[0]["molecule_chembl_id"] == "CHEMBL1"
    assert saved_records[0]["pubchem_cid"] == 123

    assert run.source.source_name == "PubChem"
    assert run.raw_file.record_count == 1

    assert manifest["source"]["source_name"] == "PubChem"
    assert manifest["raw_file"]["record_count"] == 1
    assert manifest["raw_file"]["sha256"]
