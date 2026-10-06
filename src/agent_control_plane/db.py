"""PostgreSQL is the canonical ACP state store and task/run ledger."""

from contextlib import contextmanager
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

WORKER_LOCK = (174092, 2)
PERSONAL_WORKER_LOCK = (174092, 3)
DIAGNOSTIC = "quantum-platform-pod-readiness"
SCHEMA_VERSION = 3
FIELDS = """
 t.id AS task_id, t.tenant, t.requested_by, t.kind, t.diagnostic,
 t.conversation_id, t.input_message_id, t.created_at,
 r.id AS run_id, r.status, r.profile, r.model, r.runtime_revision, r.session_id,
 r.started_at, r.finished_at, r.evidence, r.summary, r.failure_code
"""


@contextmanager
def connection(dsn):
    with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5, autocommit=True) as conn:
        yield conn


@contextmanager
def scoped(conn, tenant, subject=None, worker_role=None):
    with conn.transaction():
        conn.execute("SELECT set_config('acp.tenant_id', %s, true)", (tenant,))
        if subject is not None:
            conn.execute("SELECT set_config('acp.subject_id', %s, true)", (subject,))
        if worker_role is not None:
            conn.execute("SELECT set_config('acp.worker_role', %s, true)", (worker_role,))
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
            "SELECT id FROM acp1.task "
            "WHERE kind='admin_diagnostic' AND requested_by=%s AND idempotency_key=%s",
            (principal.subject, key),
        ).fetchone()
        if existing:
            return existing["id"], False
        active = conn.execute(
            "SELECT count(*) AS total, count(*) FILTER (WHERE t.requested_by=%s) AS mine "
            "FROM acp1.run r JOIN acp1.task t ON t.id=r.task_id "
            "WHERE t.kind='admin_diagnostic' AND r.status IN ('queued','running')",
            (principal.subject,),
        ).fetchone()
        if active["total"] >= 20 or active["mine"] >= 1:
            raise QueueFull
        task_id, run_id = uuid4(), uuid4()
        conn.execute(
            "INSERT INTO acp1.task"
            "(id,tenant,requested_by,idempotency_key,kind,diagnostic) "
            "VALUES (%s,%s,%s,%s,'admin_diagnostic',%s)",
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
            f"SELECT {FIELDS} FROM acp1.task t JOIN acp1.run r ON r.task_id=t.id "
            "WHERE t.kind='admin_diagnostic' AND t.id=%s",
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
            "WHERE t.kind='admin_diagnostic' "
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
            (conversation_id, principal.tenant, principal.subject, project_id, title),
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
                "SELECT id,sequence,author_kind,content,source_channel,"
                "client_message_id,run_id,created_at "
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
                "SELECT id,sequence,author_kind,content,source_channel,"
                "client_message_id,run_id,created_at "
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
            "RETURNING id,sequence,author_kind,content,source_channel,"
            "client_message_id,run_id,created_at",
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
        _touch_context(conn, conversation_id)
        return row


def _touch_context(conn, conversation_id):
    conn.execute(
        "UPDATE acp1.conversation SET updated_at=now() WHERE id=%s",
        (conversation_id,),
    )
    project = conn.execute(
        "SELECT project_id FROM acp1.conversation WHERE id=%s",
        (conversation_id,),
    ).fetchone()
    if project and project["project_id"] is not None:
        conn.execute(
            "UPDATE acp1.project SET updated_at=now() WHERE id=%s",
            (project["project_id"],),
        )


def create_turn(
    conn,
    principal,
    conversation_id,
    *,
    key,
    content,
    source_channel,
    client_message_id=None,
):
    with scoped(conn, principal.tenant, principal.subject):
        conversation = conn.execute(
            "SELECT id FROM acp1.conversation WHERE id=%s AND archived_at IS NULL FOR UPDATE",
            (conversation_id,),
        ).fetchone()
        if conversation is None:
            return None, False
        existing = conn.execute(
            "SELECT t.id AS task_id,r.id AS run_id,m.id AS message_id,m.sequence,"
            "r.status,r.profile,r.failure_code "
            "FROM acp1.task t JOIN acp1.run r ON r.task_id=t.id "
            "JOIN acp1.message m ON m.id=t.input_message_id "
            "WHERE t.kind='personal_turn' AND t.requested_by=%s AND t.idempotency_key=%s",
            (principal.subject, key),
        ).fetchone()
        if existing:
            return existing, False
        if client_message_id is not None:
            message = conn.execute(
                "SELECT id FROM acp1.message "
                "WHERE conversation_id=%s AND client_message_id=%s",
                (conversation_id, client_message_id),
            ).fetchone()
            if message:
                existing = conn.execute(
                    "SELECT t.id AS task_id,r.id AS run_id,m.id AS message_id,m.sequence,"
                    "r.status,r.profile,r.failure_code "
                    "FROM acp1.task t JOIN acp1.run r ON r.task_id=t.id "
                    "JOIN acp1.message m ON m.id=t.input_message_id "
                    "WHERE t.kind='personal_turn' AND t.input_message_id=%s",
                    (message["id"],),
                ).fetchone()
                if existing:
                    return existing, False
        active = conn.execute(
            "SELECT count(*) AS n FROM acp1.run r JOIN acp1.task t ON t.id=r.task_id "
            "WHERE t.kind='personal_turn' AND t.requested_by=%s "
            "AND r.status IN ('queued','running')",
            (principal.subject,),
        ).fetchone()["n"]
        if active >= 4:
            raise QueueFull

        sequence = conn.execute(
            "SELECT COALESCE(max(sequence),0)+1 AS sequence FROM acp1.message "
            "WHERE conversation_id=%s",
            (conversation_id,),
        ).fetchone()["sequence"]
        message_id, task_id, run_id = uuid4(), uuid4(), uuid4()
        conn.execute(
            "INSERT INTO acp1.message"
            "(id,tenant,owner_subject,conversation_id,sequence,author_kind,content,"
            "source_channel,client_message_id) "
            "VALUES (%s,%s,%s,%s,%s,'user',%s,%s,%s)",
            (
                message_id,
                principal.tenant,
                principal.subject,
                conversation_id,
                sequence,
                Jsonb(content),
                source_channel,
                client_message_id,
            ),
        )
        conn.execute(
            "INSERT INTO acp1.task"
            "(id,tenant,requested_by,idempotency_key,kind,conversation_id,input_message_id) "
            "VALUES (%s,%s,%s,%s,'personal_turn',%s,%s)",
            (
                task_id,
                principal.tenant,
                principal.subject,
                key,
                conversation_id,
                message_id,
            ),
        )
        conn.execute(
            "INSERT INTO acp1.run(id,tenant,task_id,status,profile) "
            "VALUES (%s,%s,%s,'queued','personal-general')",
            (run_id, principal.tenant, task_id),
        )
        event(
            conn,
            principal.tenant,
            run_id,
            "queued",
            {"actor": principal.subject, "conversation_id": str(conversation_id)},
        )
        _touch_context(conn, conversation_id)
        return {
            "task_id": task_id,
            "run_id": run_id,
            "message_id": message_id,
            "sequence": sequence,
            "status": "queued",
            "profile": "personal-general",
            "failure_code": None,
        }, True


def run_detail(conn, principal, run_id):
    with scoped(conn, principal.tenant, principal.subject):
        row = conn.execute(
            "SELECT r.id AS run_id,r.status,r.profile,r.model,r.runtime_revision,"
            "r.session_id,r.started_at,r.finished_at,r.summary,r.failure_code,"
            "t.id AS task_id,t.conversation_id,t.input_message_id "
            "FROM acp1.run r JOIN acp1.task t ON t.id=r.task_id "
            "WHERE t.kind='personal_turn' AND r.id=%s",
            (run_id,),
        ).fetchone()
        if row:
            row["events"] = conn.execute(
                "SELECT id,kind,occurred_at,data FROM acp1.event WHERE run_id=%s ORDER BY id",
                (run_id,),
            ).fetchall()
        return row


def recover_interrupted(conn, tenant):
    with scoped(conn, tenant):
        rows = conn.execute(
            "UPDATE acp1.run r SET status='failed',failure_code='worker_interrupted',"
            "finished_at=now() FROM acp1.task t "
            "WHERE r.task_id=t.id AND t.kind='admin_diagnostic' "
            "AND r.status='running' RETURNING r.id"
        ).fetchall()
        for row in rows:
            event(conn, tenant, row["id"], "failed", {"code": "worker_interrupted"})


def recover_interrupted_personal(conn, tenant):
    with scoped(conn, tenant, worker_role="personal"):
        rows = conn.execute(
            "UPDATE acp1.run r SET status='failed',failure_code='worker_interrupted',"
            "finished_at=now() FROM acp1.task t "
            "WHERE r.task_id=t.id AND t.kind='personal_turn' "
            "AND r.status='running' RETURNING r.id"
        ).fetchall()
        for row in rows:
            event(conn, tenant, row["id"], "failed", {"code": "worker_interrupted"})


def claim(conn, settings, revision):
    with scoped(conn, settings.tenant):
        row = conn.execute(
            "SELECT r.id,r.task_id FROM acp1.run r JOIN acp1.task t ON t.id=r.task_id "
            "WHERE t.kind='admin_diagnostic' AND r.status='queued' "
            "ORDER BY t.created_at,t.id FOR UPDATE OF r SKIP LOCKED LIMIT 1"
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE acp1.run SET status='running',started_at=now(),model=%s,"
                "runtime_revision=%s,session_id=%s WHERE id=%s",
                (settings.model, revision, f"acp-{row['id']}", row["id"]),
            )
            event(conn, settings.tenant, row["id"], "started")
        return row


def claim_personal(conn, settings, revision):
    with scoped(conn, settings.tenant, worker_role="personal"):
        row = conn.execute(
            "SELECT r.id,r.task_id,t.requested_by,t.conversation_id,t.input_message_id,"
            "m.sequence AS input_sequence "
            "FROM acp1.run r JOIN acp1.task t ON t.id=r.task_id "
            "JOIN acp1.message m ON m.id=t.input_message_id "
            "WHERE t.kind='personal_turn' AND r.status='queued' "
            "ORDER BY t.created_at,t.id FOR UPDATE OF r SKIP LOCKED LIMIT 1"
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE acp1.run SET status='running',started_at=now(),model=%s,"
                "runtime_revision=%s,session_id=%s WHERE id=%s",
                (settings.model, revision, f"acp-{row['id']}", row["id"]),
            )
            event(conn, settings.tenant, row["id"], "started")
        return row


def hydrate_personal_context(conn, tenant, run):
    with scoped(conn, tenant, worker_role="personal"):
        conversation = conn.execute(
            "SELECT id,project_id,title,owner_subject FROM acp1.conversation "
            "WHERE id=%s AND owner_subject=%s",
            (run["conversation_id"], run["requested_by"]),
        ).fetchone()
        if conversation is None:
            raise RuntimeError("Personal conversation is unavailable")
        messages = conn.execute(
            "SELECT id,sequence,author_kind,content,source_channel,created_at "
            "FROM acp1.message WHERE conversation_id=%s AND sequence<=%s ORDER BY sequence",
            (run["conversation_id"], run["input_sequence"]),
        ).fetchall()
        return {"conversation": conversation, "messages": messages}


def finish_personal(conn, tenant, run, response, *, failure=None):
    with scoped(conn, tenant, worker_role="personal"):
        status = "failed" if failure else "succeeded"
        changed = conn.execute(
            "UPDATE acp1.run SET status=%s,summary=%s,failure_code=%s,finished_at=now() "
            "WHERE id=%s AND status='running' RETURNING id",
            (status, response if not failure else None, failure, run["id"]),
        ).fetchone()
        if not changed:
            raise RuntimeError("Run no longer owned by this worker")
        if failure:
            event(conn, tenant, run["id"], "failed", {"code": failure})
            return

        sequence = conn.execute(
            "SELECT COALESCE(max(sequence),0)+1 AS sequence FROM acp1.message "
            "WHERE conversation_id=%s",
            (run["conversation_id"],),
        ).fetchone()["sequence"]
        conn.execute(
            "INSERT INTO acp1.message"
            "(id,tenant,owner_subject,conversation_id,sequence,author_kind,content,"
            "source_channel,run_id) "
            "VALUES (%s,%s,%s,%s,%s,'assistant',%s,'system',%s)",
            (
                uuid4(),
                tenant,
                run["requested_by"],
                run["conversation_id"],
                sequence,
                Jsonb({"text": response}),
                run["id"],
            ),
        )
        _touch_context(conn, run["conversation_id"])
        event(conn, tenant, run["id"], "succeeded")


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
