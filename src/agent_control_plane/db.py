"""PostgreSQL is both the Phase 1 queue and canonical run ledger."""

from contextlib import contextmanager
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

WORKER_LOCK = (174092, 2)
DIAGNOSTIC = "quantum-platform-pod-readiness"
FIELDS = """
 t.id AS task_id, t.tenant, t.requested_by, t.diagnostic, t.created_at,
 r.id AS run_id, r.status, r.profile, r.model, r.runtime_revision, r.session_id,
 r.started_at, r.finished_at, r.evidence, r.summary, r.failure_code
"""


@contextmanager
def connection(dsn):
    with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5, autocommit=True) as conn:
        yield conn


@contextmanager
def scoped(conn, tenant):
    with conn.transaction():
        conn.execute("SELECT set_config('acp.tenant_id', %s, true)", (tenant,))
        conn.execute("SET LOCAL statement_timeout = '5s'")
        yield


def ready(conn):
    role = conn.execute(
        "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
    ).fetchone()
    if role["rolsuper"] or role["rolbypassrls"]:
        raise RuntimeError("Application database role must enforce RLS")
    version = conn.execute("SELECT version FROM acp1.schema_version").fetchone()
    if version != {"version": 1}:
        raise RuntimeError("Database migration is required")


def event(conn, tenant, run_id, kind, data=None):
    conn.execute(
        "INSERT INTO acp1.event(tenant,run_id,kind,data) VALUES (%s,%s,%s,%s)",
        (tenant, run_id, kind, Jsonb(data or {})),
    )


class QueueFull(Exception):
    pass


def create_task(conn, principal, key):
    with scoped(conn, principal.tenant):
        # Serialize queue admission per tenant, including idempotent retries.
        conn.execute("SELECT pg_advisory_xact_lock(174093, hashtext(%s))", (principal.tenant,))
        existing = conn.execute(
            "SELECT id FROM acp1.task WHERE requested_by=%s AND idempotency_key=%s",
            (principal.subject, key),
        ).fetchone()
        if existing:
            return existing["id"], False
        active = conn.execute(
            "SELECT count(*) AS total, count(*) FILTER (WHERE t.requested_by=%s) AS mine "
            "FROM acp1.run r JOIN acp1.task t ON t.id=r.task_id "
            "WHERE r.status IN ('queued','running')",
            (principal.subject,),
        ).fetchone()
        if active["total"] >= 20 or active["mine"] >= 1:
            raise QueueFull
        task_id, run_id = uuid4(), uuid4()
        conn.execute(
            "INSERT INTO acp1.task(id,tenant,requested_by,idempotency_key,diagnostic) "
            "VALUES (%s,%s,%s,%s,%s)",
            (task_id, principal.tenant, principal.subject, key, DIAGNOSTIC),
        )
        conn.execute(
            "INSERT INTO acp1.run(id,tenant,task_id,status,profile) "
            "VALUES (%s,%s,%s,'queued','admin-readonly')",
            (run_id, principal.tenant, task_id),
        )
        event(conn, principal.tenant, run_id, "queued", {"actor": principal.subject})
        return task_id, True


def task_detail(conn, tenant, task_id):
    with scoped(conn, tenant):
        row = conn.execute(
            f"SELECT {FIELDS} FROM acp1.task t JOIN acp1.run r ON r.task_id=t.id WHERE t.id=%s",
            (task_id,),
        ).fetchone()
        if row:
            row["events"] = conn.execute(
                "SELECT id,kind,occurred_at,data FROM acp1.event WHERE run_id=%s ORDER BY id",
                (row["run_id"],),
            ).fetchall()
        return row


def list_tasks(conn, tenant, offset):
    with scoped(conn, tenant):
        return conn.execute(
            f"SELECT {FIELDS} FROM acp1.task t JOIN acp1.run r ON r.task_id=t.id "
            "ORDER BY t.created_at DESC,t.id DESC LIMIT 50 OFFSET %s",
            (offset,),
        ).fetchall()


def recover_interrupted(conn, tenant):
    with scoped(conn, tenant):
        rows = conn.execute(
            "UPDATE acp1.run SET status='failed', failure_code='worker_interrupted', "
            "finished_at=now() WHERE status='running' RETURNING id"
        ).fetchall()
        for row in rows:
            event(conn, tenant, row["id"], "failed", {"code": "worker_interrupted"})


def claim(conn, settings, revision):
    with scoped(conn, settings.tenant):
        row = conn.execute(
            "SELECT r.id,r.task_id FROM acp1.run r JOIN acp1.task t ON t.id=r.task_id "
            "WHERE r.status='queued' ORDER BY t.created_at,t.id "
            "FOR UPDATE OF r SKIP LOCKED LIMIT 1"
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE acp1.run SET status='running',started_at=now(),model=%s,"
                "runtime_revision=%s,session_id=%s WHERE id=%s",
                (settings.model, revision, f"acp-{row['id']}", row["id"]),
            )
            event(conn, settings.tenant, row["id"], "started")
        return row


def save_evidence(conn, tenant, run_id, evidence):
    with scoped(conn, tenant):
        conn.execute("UPDATE acp1.run SET evidence=%s WHERE id=%s", (Jsonb(evidence), run_id))
        event(conn, tenant, run_id, "diagnostic_completed", {"tool": DIAGNOSTIC})


def finish(conn, tenant, run_id, *, summary=None, failure=None):
    with scoped(conn, tenant):
        status = "failed" if failure else "succeeded"
        changed = conn.execute(
            "UPDATE acp1.run SET status=%s,summary=%s,failure_code=%s,finished_at=now() "
            "WHERE id=%s AND status='running' RETURNING id",
            (status, summary, failure, run_id),
        ).fetchone()
        if not changed:
            raise RuntimeError("Run no longer owned by this worker")
        event(conn, tenant, run_id, status, {"code": failure} if failure else {})
