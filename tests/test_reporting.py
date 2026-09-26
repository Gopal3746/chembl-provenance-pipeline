import json

from drug_catalog.batch_enrichment import (
    BatchEnrichmentResult,
    EnrichmentFailure,
)
from drug_catalog.conflicts import DuplicateSummary
from drug_catalog.models import CompoundRecord
from drug_catalog.normalization import (
    RejectedActivity,
    RejectionReason,
)
from drug_catalog.reporting import (
    build_catalog_quality_report,
    save_catalog_quality_report,
)


def test_build_catalog_quality_report(tmp_path) -> None:
    rejected = [
        RejectedActivity(
            record={"activity_id": 1},
            reason=RejectionReason.MISSING_OR_INVALID_VALUE,
        )
    ]

    enrichment_result = BatchEnrichmentResult(
        compounds=[
            CompoundRecord(
                molecule_chembl_id="CHEMBL1",
                pubchem_cid=123,
                molecular_formula="C10H10",
                molecular_weight=130.19,
                smiles="CC",
                connectivity_smiles="CC",
                inchi="InChI=1S/example",
                inchikey="TEST-KEY",
                iupac_name="example",
            )
        ],
        failures=[
            EnrichmentFailure(
                molecule_chembl_id="CHEMBL2",
                reason="pubchem_not_found",
            )
        ],
    )

    duplicate_summary = DuplicateSummary(
        exact_duplicate_groups=1,
        repeated_measurement_groups=2,
        conflicting_measurement_groups=1,
        conflicts=[],
    )

    report = build_catalog_quality_report(
        raw_activity_count=10,
        normalized_activity_count=9,
        rejected=rejected,
        unique_compound_count=2,
        enrichment_result=enrichment_result,
        duplicate_summary=duplicate_summary,
    )

    assert report.raw_activity_records == 10
    assert report.normalized_activity_records == 9
    assert report.rejected_activity_records == 1

    assert report.rejection_reasons == {
        "missing_or_invalid_value": 1
    }

    assert report.unique_compounds == 2
    assert report.enriched_compounds == 1
    assert report.enrichment_failures == 1

    assert report.repeated_measurement_groups == 2
    assert report.exact_duplicate_groups == 1
    assert report.conflicting_measurement_groups == 1

    output_path = tmp_path / "quality-report.json"

    save_catalog_quality_report(
        report,
        output_path,
    )

    saved = json.loads(output_path.read_text())

    assert saved["raw_activity_records"] == 10
    assert saved["normalized_activity_records"] == 9
