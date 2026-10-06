"""Ordered database migrations. Run only with the schema-owner credential."""

import hashlib
import os
from importlib.resources import files

import psycopg

MIGRATIONS = (
    (1, "schema.sql"),
    (2, "migrations/0002_m4a_personal_agent.sql"),
)


def _migration(version, resource):
    sql = files("agent_control_plane").joinpath(resource).read_text()
    return version, sql, hashlib.sha256(sql.encode()).hexdigest()


def migrate(dsn):
    with psycopg.connect(dsn) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(174092, 1)")
        conn.execute("CREATE SCHEMA IF NOT EXISTS acp1")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS acp1.schema_version "
            "(version integer PRIMARY KEY, checksum text NOT NULL)"
        )
        installed = dict(conn.execute(
            "SELECT version, checksum FROM acp1.schema_version ORDER BY version"
        ).fetchall())

        known_versions = {version for version, _ in MIGRATIONS}
        unknown = set(installed) - known_versions
        if unknown:
            raise RuntimeError(f"Database has unknown schema versions: {sorted(unknown)}")

        for version, resource in MIGRATIONS:
            _, sql, checksum = _migration(version, resource)
            if version in installed:
                if installed[version] != checksum:
                    raise RuntimeError(
                        f"Schema version {version} checksum mismatch; historical migrations "
                        "must never be edited"
                    )
                continue
            if any(existing > version for existing in installed):
                raise RuntimeError("Database migration history contains a gap")
            conn.execute(sql)
            conn.execute(
                "INSERT INTO acp1.schema_version(version, checksum) VALUES (%s, %s)",
                (version, checksum),
            )
            installed[version] = checksum

        conn.execute("GRANT SELECT ON acp1.schema_version TO acp_app")


if __name__ == "__main__":
    migrate(os.environ["ACP_MIGRATION_DATABASE_URL"])
