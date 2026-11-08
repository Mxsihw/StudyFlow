import os
import uuid

import psycopg
from psycopg.conninfo import make_conninfo

import database


def get_base_test_database_url():
    """Return the PostgreSQL DSN used to create isolated test schemas."""
    return (
        os.environ.get("STUDYFLOW_TEST_DB_URL")
        or os.environ.get("STUDYFLOW_DB_URL")
        or database.DEFAULT_DATABASE_URL
    )


def create_test_schema():
    """Create an isolated schema and return (DSN, schema name)."""
    base_url = get_base_test_database_url()
    schema = f"studyflow_test_{uuid.uuid4().hex[:12]}"

    with psycopg.connect(base_url, autocommit=True) as connection:
        connection.execute(f'CREATE SCHEMA "{schema}"')

    test_url = make_conninfo(
        base_url,
        options=f"-c search_path={schema}",
    )

    return test_url, schema


def drop_test_schema(schema):
    """Drop an isolated test schema and all objects inside it."""
    base_url = get_base_test_database_url()

    with psycopg.connect(base_url, autocommit=True) as connection:
        connection.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
