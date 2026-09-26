CREATE TABLE IF NOT EXISTS sources (
    source_id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_version TEXT,
    endpoint TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,

    source_id BIGINT NOT NULL
        REFERENCES sources(source_id),

    retrieved_at TIMESTAMPTZ NOT NULL,

    query_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,

    raw_file_path TEXT NOT NULL,
    raw_file_sha256 TEXT NOT NULL,

    record_count INTEGER NOT NULL
        CHECK (record_count >= 0),

    pipeline_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS compounds (
    compound_id BIGSERIAL PRIMARY KEY,

    molecule_chembl_id TEXT NOT NULL UNIQUE,
    pubchem_cid BIGINT,

    molecular_formula TEXT,
    molecular_weight DOUBLE PRECISION,

    smiles TEXT,
    connectivity_smiles TEXT,

    inchi TEXT,
    inchikey TEXT NOT NULL,

    iupac_name TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_compounds_inchikey
    ON compounds(inchikey);


CREATE INDEX IF NOT EXISTS idx_compounds_pubchem_cid
    ON compounds(pubchem_cid);


CREATE TABLE IF NOT EXISTS targets (
    target_id BIGSERIAL PRIMARY KEY,

    target_chembl_id TEXT NOT NULL UNIQUE,
    preferred_name TEXT,

    target_type TEXT,
    organism TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS assays (
    assay_id BIGSERIAL PRIMARY KEY,

    assay_chembl_id TEXT NOT NULL UNIQUE,

    target_id BIGINT
        REFERENCES targets(target_id),

    assay_type TEXT,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS activities (
    activity_id BIGINT PRIMARY KEY,

    compound_id BIGINT NOT NULL
        REFERENCES compounds(compound_id),

    target_id BIGINT NOT NULL
        REFERENCES targets(target_id),

    assay_id BIGINT
        REFERENCES assays(assay_id),

    document_chembl_id TEXT,

    activity_type TEXT NOT NULL,
    activity_value NUMERIC NOT NULL,
    activity_units TEXT NOT NULL,

    relation TEXT,
    pchembl_value NUMERIC,

    ingestion_run_id TEXT
        REFERENCES ingestion_runs(run_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_activities_compound
    ON activities(compound_id);


CREATE INDEX IF NOT EXISTS idx_activities_target
    ON activities(target_id);


CREATE INDEX IF NOT EXISTS idx_activities_assay
    ON activities(assay_id);


CREATE INDEX IF NOT EXISTS idx_activities_type
    ON activities(activity_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_identity
    ON sources (
        source_name,
        COALESCE(source_version, ''),
        endpoint
    );
