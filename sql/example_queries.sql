-- ============================================================
-- Drug Discovery Data Catalog
-- Example analytical queries
-- ============================================================


-- 1. Most potent EGFR IC50 measurements.
--
-- Activity values should only be ranked when the measurement
-- type and units are comparable. This query therefore restricts
-- the result to IC50 measurements reported in nM rather than
-- sorting IC50, Ki, Kd, and EC50 values together.

SELECT
    c.molecule_chembl_id,
    c.pubchem_cid,
    c.molecular_formula,
    a.activity_type,
    a.activity_value,
    a.activity_units,
    ass.assay_chembl_id
FROM activities AS a
JOIN compounds AS c
    ON c.compound_id = a.compound_id
JOIN targets AS t
    ON t.target_id = a.target_id
LEFT JOIN assays AS ass
    ON ass.assay_id = a.assay_id
WHERE t.target_chembl_id = 'CHEMBL203'
  AND a.activity_type = 'IC50'
  AND a.activity_units = 'nM'
ORDER BY a.activity_value ASC
LIMIT 20;


-- 2. Activity measurements by type.

SELECT
    activity_type,
    activity_units,
    COUNT(*) AS measurement_count
FROM activities
GROUP BY
    activity_type,
    activity_units
ORDER BY
    measurement_count DESC;


-- 3. Compounds with measurements from multiple assays.
--
-- Multiple measurements for the same compound are not
-- automatically conflicts. Measurements produced by different
-- assays represent different experimental contexts.

SELECT
    c.molecule_chembl_id,
    COUNT(*) AS measurement_count,
    COUNT(DISTINCT ass.assay_chembl_id) AS assay_count
FROM activities AS a
JOIN compounds AS c
    ON c.compound_id = a.compound_id
LEFT JOIN assays AS ass
    ON ass.assay_id = a.assay_id
GROUP BY
    c.molecule_chembl_id
HAVING COUNT(*) > 1
ORDER BY
    measurement_count DESC
LIMIT 20;


-- 4. Source and ingestion provenance.

SELECT
    s.source_name,
    s.source_version,
    s.endpoint,
    r.run_id,
    r.retrieved_at,
    r.raw_file_path,
    r.raw_file_sha256,
    r.raw_record_count
FROM ingestion_runs AS r
JOIN sources AS s
    ON s.source_id = r.source_id
ORDER BY
    r.retrieved_at DESC;


-- 5. Trace activity records back to the source ingestion run.

SELECT
    c.molecule_chembl_id,
    t.target_chembl_id,
    ass.assay_chembl_id,
    a.activity_type,
    a.activity_value,
    a.activity_units,
    s.source_name,
    s.source_version,
    r.run_id
FROM activities AS a
JOIN compounds AS c
    ON c.compound_id = a.compound_id
JOIN targets AS t
    ON t.target_id = a.target_id
LEFT JOIN assays AS ass
    ON ass.assay_id = a.assay_id
JOIN ingestion_runs AS r
    ON r.run_id = a.ingestion_run_id
JOIN sources AS s
    ON s.source_id = r.source_id
LIMIT 50;
