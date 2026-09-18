"""Run once with the schema-owner credential, never inside an API request."""

import hashlib
import os
from importlib.resources import files

import psycopg


def migrate(dsn):
    sql = files("agent_control_plane").joinpath("schema.sql").read_text()
    checksum = hashlib.sha256(sql.encode()).hexdigest()
    with psycopg.connect(dsn) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(174092, 1)")
        conn.execute("CREATE SCHEMA IF NOT EXISTS acp1")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS acp1.schema_version "
            "(version integer PRIMARY KEY, checksum text NOT NULL)"
        )
        versions = conn.execute("SELECT version, checksum FROM acp1.schema_version").fetchall()
        if versions:
            if versions != [(1, checksum)]:
                raise RuntimeError("Schema version/checksum mismatch; explicit migration required")
            return
        conn.execute(sql)
        conn.execute("INSERT INTO acp1.schema_version VALUES (1, %s)", (checksum,))
        conn.execute("GRANT SELECT ON acp1.schema_version TO acp_app")


if __name__ == "__main__":
    migrate(os.environ["ACP_MIGRATION_DATABASE_URL"])
