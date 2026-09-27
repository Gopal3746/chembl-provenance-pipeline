-- Most potent EGFR measurements
SELECT
    c.molecule_chembl_id,
    c.pubchem_cid,
    c.molecular_formula,
    a.activity_type,
    a.activity_value,
    a.activity_units,
    s.assay_chembl_id
FROM activities a
JOIN compounds c
    ON c.compound_id = a.compound_id
JOIN targets t
    ON t.target_id = a.target_id
LEFT JOIN assays s
    ON s.assay_id = a.assay_id
WHERE t.target_chembl_id = 'CHEMBL203'
ORDER BY a.activity_value ASC
LIMIT 10;


-- Activity counts by measurement type
SELECT
    activity_type,
    COUNT(*) AS activity_count
FROM activities
GROUP BY activity_type
ORDER BY activity_count DESC;


-- Compounds with multiple activity measurements
SELECT
    c.molecule_chembl_id,
    COUNT(*) AS measurement_count,
    MIN(a.activity_value) AS minimum_value,
    MAX(a.activity_value) AS maximum_value
FROM activities a
JOIN compounds c
    ON c.compound_id = a.compound_id
GROUP BY c.molecule_chembl_id
HAVING COUNT(*) > 1
ORDER BY measurement_count DESC;


-- Provenance of source ingestion runs
SELECT
    ir.run_id,
    s.source_name,
    ir.record_count,
    ir.pipeline_version,
    ir.retrieved_at,
    ir.raw_file_sha256
FROM ingestion_runs ir
JOIN sources s
    ON s.source_id = ir.source_id
ORDER BY ir.retrieved_at;


-- Activities with source lineage
SELECT
    a.activity_id,
    c.molecule_chembl_id,
    t.target_chembl_id,
    a.activity_type,
    a.activity_value,
    a.activity_units,
    ir.run_id,
    src.source_name,
    ir.raw_file_sha256
FROM activities a
JOIN compounds c
    ON c.compound_id = a.compound_id
JOIN targets t
    ON t.target_id = a.target_id
LEFT JOIN ingestion_runs ir
    ON ir.run_id = a.ingestion_run_id
LEFT JOIN sources src
    ON src.source_id = ir.source_id
ORDER BY a.activity_id;
