"""PostgreSQL is the canonical ACP state store and Phase 1 queue/run ledger."""

from contextlib import contextmanager
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

WORKER_LOCK = (174092, 2)
DIAGNOSTIC = "quantum-platform-pod-readiness"
SCHEMA_VERSION = 2
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
def scoped(conn, tenant, subject=None):
    with conn.transaction():
        conn.execute("SELECT set_config('acp.tenant_id', %s, true)", (tenant,))
        if subject is not None:
            conn.execute("SELECT set_config('acp.subject_id', %s, true)", (subject,))
        conn.execute("SET LOCAL statement_timeout = '5s'")
        yield


def ready(conn):
    role = conn.execute(
        "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
    ).fetchone()
    if role["rolsuper"] or role["rolbypassrls"]:
        raise RuntimeError("Application database role must enforce RLS")
    version = conn.execute(
        "SELECT version FROM acp1.schema_version ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if version != {"version": SCHEMA_VERSION}:
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


def create_project(conn, principal, title):
    project_id = uuid4()
    with scoped(conn, principal.tenant, principal.subject):
        return conn.execute(
            "INSERT INTO acp1.project(id,tenant,owner_subject,title) VALUES (%s,%s,%s,%s) "
            "RETURNING id,title,created_at,updated_at,archived_at",
            (project_id, principal.tenant, principal.subject, title),
        ).fetchone()


def list_projects(conn, principal):
    with scoped(conn, principal.tenant, principal.subject):
        return conn.execute(
            "SELECT id,title,created_at,updated_at,archived_at FROM acp1.project "
            "ORDER BY updated_at DESC,id DESC LIMIT 100"
        ).fetchall()


def create_conversation(conn, principal, title, project_id=None):
    conversation_id = uuid4()
    with scoped(conn, principal.tenant, principal.subject):
        if project_id is not None:
            project = conn.execute(
                "SELECT id FROM acp1.project WHERE id=%s AND archived_at IS NULL",
                (project_id,),
            ).fetchone()
            if project is None:
                return None
        return conn.execute(
            "INSERT INTO acp1.conversation"
            "(id,tenant,owner_subject,project_id,title) VALUES (%s,%s,%s,%s,%s) "
            "RETURNING id,project_id,title,created_at,updated_at,archived_at",
            (
                conversation_id,
                principal.tenant,
                principal.subject,
                project_id,
                title,
            ),
        ).fetchone()


def list_conversations(conn, principal, project_id=None):
    with scoped(conn, principal.tenant, principal.subject):
        if project_id is None:
            return conn.execute(
                "SELECT id,project_id,title,created_at,updated_at,archived_at "
                "FROM acp1.conversation ORDER BY updated_at DESC,id DESC LIMIT 100"
            ).fetchall()
        return conn.execute(
            "SELECT id,project_id,title,created_at,updated_at,archived_at "
            "FROM acp1.conversation WHERE project_id=%s "
            "ORDER BY updated_at DESC,id DESC LIMIT 100",
            (project_id,),
        ).fetchall()


def conversation_detail(conn, principal, conversation_id):
    with scoped(conn, principal.tenant, principal.subject):
        row = conn.execute(
            "SELECT id,project_id,title,created_at,updated_at,archived_at "
            "FROM acp1.conversation WHERE id=%s",
            (conversation_id,),
        ).fetchone()
        if row:
            row["messages"] = conn.execute(
                "SELECT id,sequence,author_kind,content,source_channel,client_message_id,created_at "
                "FROM acp1.message WHERE conversation_id=%s ORDER BY sequence",
                (conversation_id,),
            ).fetchall()
        return row


def append_message(
    conn,
    principal,
    conversation_id,
    *,
    author_kind,
    content,
    source_channel,
    client_message_id=None,
):
    message_id = uuid4()
    with scoped(conn, principal.tenant, principal.subject):
        conversation = conn.execute(
            "SELECT id FROM acp1.conversation WHERE id=%s AND archived_at IS NULL FOR UPDATE",
            (conversation_id,),
        ).fetchone()
        if conversation is None:
            return None
        if client_message_id is not None:
            existing = conn.execute(
                "SELECT id,sequence,author_kind,content,source_channel,client_message_id,created_at "
                "FROM acp1.message WHERE conversation_id=%s AND client_message_id=%s",
                (conversation_id, client_message_id),
            ).fetchone()
            if existing:
                return existing
        sequence = conn.execute(
            "SELECT COALESCE(max(sequence),0)+1 AS sequence FROM acp1.message "
            "WHERE conversation_id=%s",
            (conversation_id,),
        ).fetchone()["sequence"]
        row = conn.execute(
            "INSERT INTO acp1.message"
            "(id,tenant,owner_subject,conversation_id,sequence,author_kind,content,"
            "source_channel,client_message_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "RETURNING id,sequence,author_kind,content,source_channel,client_message_id,created_at",
            (
                message_id,
                principal.tenant,
                principal.subject,
                conversation_id,
                sequence,
                author_kind,
                Jsonb(content),
                source_channel,
                client_message_id,
            ),
        ).fetchone()
        conn.execute(
            "UPDATE acp1.conversation SET updated_at=now() WHERE id=%s",
            (conversation_id,),
        )
        if conn.execute(
            "SELECT project_id FROM acp1.conversation WHERE id=%s", (conversation_id,)
        ).fetchone()["project_id"] is not None:
            conn.execute(
                "UPDATE acp1.project SET updated_at=now() WHERE id=("
                "SELECT project_id FROM acp1.conversation WHERE id=%s)",
                (conversation_id,),
            )
        return row


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
