from dataclasses import replace
from uuid import uuid4

import psycopg
import pytest

from agent_control_plane import db
from agent_control_plane.auth import Principal
from agent_control_plane.diagnostic import DiagnosticFailure
from agent_control_plane.worker import run_once


def test_http_queue_idempotency_run_and_history(database, client, token, config):
    key = str(uuid4())
    headers = {**token(), "Idempotency-Key": key}
    body = {"diagnostic": "quantum-platform-pod-readiness"}
    created = client.post("/v1/admin/tasks", json=body, headers=headers)
    assert created.status_code == 202, created.text
    task_id = created.json()["task_id"]
    retry = client.post("/v1/admin/tasks", json=body, headers=headers)
    assert retry.status_code == 200
    assert retry.json()["task_id"] == task_id
    throttled = client.post(
        "/v1/admin/tasks", json=body, headers={**token(), "Idempotency-Key": str(uuid4())}
    )
    assert throttled.status_code == 429
    with db.connection(database) as conn:
        db.ready(conn)
        assert run_once(
            conn,
            config,
            diagnostic=lambda _: {"counts": {"true": 3, "false": 0}},
            explainer=lambda *args: "Three Ready pods were observed.",
        )
    # Reopen the DB connection through a new HTTP request: state is not process memory.
    task = client.get("/v1/admin/tasks/" + task_id, headers=token()).json()
    assert task["status"] == "succeeded"
    assert task["evidence"]["counts"]["true"] == 3
    assert [e["kind"] for e in task["events"]] == [
        "queued",
        "started",
        "diagnostic_completed",
        "succeeded",
    ]
    assert len(client.get("/v1/admin/tasks", headers=token()).json()["items"]) == 1


def test_rls_and_append_only_events(database):
    principal = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
    with db.connection(database) as conn:
        task_id, _ = db.create_task(conn, principal, uuid4())
        assert db.task_detail(conn, "another-tenant", task_id) is None
        assert db.list_tasks(conn, "another-tenant", 0) == []
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.scoped(conn, "nyameko"):
            conn.execute("UPDATE acp1.event SET kind='forged'")
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.scoped(conn, "nyameko"):
            conn.execute("DELETE FROM acp1.event")
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.scoped(conn, "another-tenant"):
            conn.execute(
                "INSERT INTO acp1.task(id,tenant,requested_by,idempotency_key,diagnostic) "
                "VALUES (%s,'nyameko','forged',%s,%s)",
                (uuid4(), uuid4(), db.DIAGNOSTIC),
            )


def test_model_failure_keeps_evidence_and_interruption_is_terminal(database, config):
    principal = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")

    def fail(*args):
        raise DiagnosticFailure("hermes_timeout")

    with db.connection(database) as conn:
        task_id, _ = db.create_task(conn, principal, uuid4())
        run_once(conn, config, diagnostic=lambda _: {"counts": {"false": 2}}, explainer=fail)
        task = db.task_detail(conn, "nyameko", task_id)
        assert task["status"] == "failed"
        assert task["failure_code"] == "hermes_timeout"
        assert task["evidence"]["counts"]["false"] == 2
        task_id, _ = db.create_task(conn, principal, uuid4())
        assert db.claim(conn, config, "test-revision")
    with db.connection(database) as conn:
        db.recover_interrupted(conn, "nyameko")
        assert db.task_detail(conn, "nyameko", task_id)["failure_code"] == "worker_interrupted"
        assert db.claim(conn, config, "test-revision") is None


def test_db_connection_does_not_retain_tenant(database, config):
    with db.connection(database) as conn:
        db.create_task(conn, Principal("test-admin", "nyameko"), uuid4())
        with db.scoped(conn, "another-tenant"):
            assert conn.execute("SELECT count(*) AS n FROM acp1.task").fetchone()["n"] == 0
        # No tenant setting outside a scoped transaction grants no rows.
        assert conn.execute("SELECT count(*) AS n FROM acp1.task").fetchone()["n"] == 0


def test_two_workers_cannot_claim_same_task(database, config):
    # Keep this native-PostgreSQL test: PGlite multiplexes a single backend connection.
    with db.connection(database) as first, db.connection(database) as second:
        db.create_task(first, Principal("test-admin", "nyameko"), uuid4())
        assert db.claim(first, config, "test")
        assert db.claim(second, replace(config, model="other"), "test") is None
        assert first.execute("SELECT pg_try_advisory_lock(%s,%s) AS ok", db.WORKER_LOCK).fetchone()[
            "ok"
        ]
        assert not second.execute(
            "SELECT pg_try_advisory_lock(%s,%s) AS ok", db.WORKER_LOCK
        ).fetchone()["ok"]
