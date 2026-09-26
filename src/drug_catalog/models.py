from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    source_name: str
    source_version: str | None = None
    endpoint: str
    query_parameters: dict[str, str] = Field(default_factory=dict)
    retrieved_at: datetime


class RawFileMetadata(BaseModel):
    file_path: str
    sha256: str
    record_count: int = Field(ge=0)


class IngestionRun(BaseModel):
    run_id: str
    source: SourceMetadata
    raw_file: RawFileMetadata
    pipeline_version: str

class CompoundRecord(BaseModel):
    molecule_chembl_id: str
    pubchem_cid: int | None = None

    molecular_formula: str | None = None
    molecular_weight: float | None = None

    smiles: str | None = None
    connectivity_smiles: str | None = None

    inchi: str | None = None
    inchikey: str

    iupac_name: str | None = None
