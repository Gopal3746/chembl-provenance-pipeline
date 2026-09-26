from drug_catalog.loaders import (
    load_activities,
    load_compounds,
    load_ingestion_run,
    load_source,
    load_target,
)


def test_loader_functions_are_available() -> None:
    assert callable(load_source)
    assert callable(load_ingestion_run)
    assert callable(load_compounds)
    assert callable(load_target)
    assert callable(load_activities)
