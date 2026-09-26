from drug_catalog.database import load_schema


def test_load_schema() -> None:
    schema = load_schema()

    assert "CREATE TABLE IF NOT EXISTS sources" in schema
    assert "CREATE TABLE IF NOT EXISTS ingestion_runs" in schema
    assert "CREATE TABLE IF NOT EXISTS compounds" in schema
    assert "CREATE TABLE IF NOT EXISTS targets" in schema
    assert "CREATE TABLE IF NOT EXISTS assays" in schema
    assert "CREATE TABLE IF NOT EXISTS activities" in schema


def test_schema_contains_provenance_relationship() -> None:
    schema = load_schema()

    assert "ingestion_run_id" in schema
    assert "REFERENCES ingestion_runs(run_id)" in schema
