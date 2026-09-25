import json

from drug_catalog.storage import save_raw_records


def test_save_raw_records_creates_raw_file_and_manifest(tmp_path) -> None:
    records = [
        {
            "activity_id": 1,
            "molecule_chembl_id": "CHEMBL1",
            "standard_type": "IC50",
            "standard_value": "10",
            "standard_units": "nM",
        },
        {
            "activity_id": 2,
            "molecule_chembl_id": "CHEMBL2",
            "standard_type": "Ki",
            "standard_value": "25",
            "standard_units": "nM",
        },
    ]

    ingestion_run = save_raw_records(
        records,
        source_name="ChEMBL",
        source_version=None,
        endpoint="https://www.ebi.ac.uk/chembl/api/data/activity.json",
        query_parameters={"target_chembl_id": "CHEMBL203"},
        output_dir=tmp_path,
        file_name="CHEMBL203_activities.json",
    )

    raw_file = tmp_path / "CHEMBL203_activities.json"
    manifest_file = tmp_path / "CHEMBL203_activities.metadata.json"

    assert raw_file.exists()
    assert manifest_file.exists()

    saved_records = json.loads(raw_file.read_text())
    manifest = json.loads(manifest_file.read_text())

    assert saved_records == records
    assert ingestion_run.raw_file.record_count == 2
    assert manifest["source"]["source_name"] == "ChEMBL"
    assert manifest["source"]["query_parameters"]["target_chembl_id"] == "CHEMBL203"
    assert manifest["raw_file"]["record_count"] == 2
    assert manifest["raw_file"]["sha256"]
