from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg import Connection

DEFAULT_DATABASE_URL = (
    "postgresql://drug_catalog:drug_catalog"
    "@localhost:5432/drug_catalog"
)


def connect(
    database_url: str = DEFAULT_DATABASE_URL,
) -> Connection:
    return psycopg.connect(database_url)


def load_schema() -> str:
    schema_path = Path(__file__).with_name("schema.sql")

    return schema_path.read_text(
        encoding="utf-8",
    )


def initialize_database(
    database_url: str = DEFAULT_DATABASE_URL,
) -> None:
    schema = load_schema()

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema)

        connection.commit()
