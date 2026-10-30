"""PostgreSQL-backed M4b schema and RLS conformance on a disposable CI database.

Never run the database fixture against production: it drops and recreates acp1.
"""
from uuid import uuid4

import psycopg
import pytest

from agent_control_plane import db


def _subject():
    return f"urn:quantum-platform:user:{uuid4()}"


def _source(conn, tenant, owner, *, author_kind="user"):
    conversation_id, message_id = uuid4(), uuid4()
    with db.scoped(conn, tenant, owner):
        conn.execute(
            "INSERT INTO acp1.conversation(id,tenant,owner_subject,title) "
            "VALUES (%s,%s,%s,'Memory test')",
            (conversation_id, tenant, owner),
        )
        conn.execute(
            "INSERT INTO acp1.message(id,tenant,owner_subject,conversation_id,"
            "sequence,author_kind,content,source_channel) "
            "VALUES (%s,%s,%s,%s,1,%s,'{}'::jsonb,'api')",
            (message_id, tenant, owner, conversation_id, author_kind),
        )
    return conversation_id, message_id


def _candidate(conn, tenant, owner, conversation_id, message_id):
    memory_id = uuid4()
    with db.scoped(conn, tenant, owner):
        conn.execute(
            "INSERT INTO acp1.memory_item(id,tenant,owner_subject,creation_key,"
            "creation_payload_sha256,kind,source_conversation_id,source_message_id,"
            "source_sha256) VALUES (%s,%s,%s,%s,%s,'preference',%s,%s,%s)",
            (
                memory_id,
                tenant,
                owner,
                uuid4(),
                "a" * 64,
                conversation_id,
                message_id,
                "b" * 64,
            ),
        )
        conn.execute(
            "INSERT INTO acp1.memory_revision(memory_id,tenant,owner_subject,"
            "revision,event_type,body,actor_subject) "
            "VALUES (%s,%s,%s,1,'candidate_created','Remember test',%s)",
            (memory_id, tenant, owner, owner),
        )
    return memory_id


def _transition(conn, tenant, owner, memory_id, revision, event_type, body):
    with db.scoped(conn, tenant, owner):
        conn.execute(
            "INSERT INTO acp1.memory_revision(memory_id,tenant,owner_subject,"
            "revision,event_type,body,actor_subject) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (memory_id, tenant, owner, revision, event_type, body, owner),
        )
        if event_type == "approved":
            assignment = "status='active',approved_at=now()"
        elif event_type == "revoked":
            assignment = "status='revoked',revoked_at=now()"
        else:
            assignment = "status='active'"
        conn.execute(
            f"UPDATE acp1.memory_item SET {assignment},current_revision=%s WHERE id=%s",
            (revision, memory_id),
        )


def test_schema_v4_and_forced_rls_isolate_user_and_tenant(database):
    owner, other = _subject(), _subject()
    tenant = "nyameko"
    with db.connection(database) as conn:
        db.ready(conn)
        conversation_id, message_id = _source(conn, tenant, owner)
        memory_id = _candidate(conn, tenant, owner, conversation_id, message_id)
        with db.scoped(conn, tenant, other):
            for table in ("memory_item", "memory_revision"):
                row = conn.execute(
                    f"SELECT count(*) AS n FROM acp1.{table}"
                ).fetchone()
                assert row["n"] == 0
            denied = conn.execute(
                "UPDATE acp1.memory_item SET status='revoked' "
                "WHERE id=%s RETURNING id",
                (memory_id,),
            ).fetchone()
            assert denied is None
        with db.scoped(conn, "different-tenant", owner):
            assert conn.execute(
                "SELECT count(*) AS n FROM acp1.memory_item"
            ).fetchone()["n"] == 0
        with db.scoped(conn, tenant, owner):
            assert conn.execute(
                "SELECT count(*) AS n FROM acp1.memory_item"
            ).fetchone()["n"] == 1
            assert conn.execute(
                "SELECT count(*) AS n FROM acp1.memory_revision"
            ).fetchone()["n"] == 1
        policies = conn.execute(
            "SELECT tablename,relrowsecurity,relforcerowsecurity "
            "FROM pg_tables JOIN pg_class ON pg_class.relname=pg_tables.tablename "
            "WHERE schemaname='acp1' "
            "AND tablename IN ('memory_item','memory_revision')"
        ).fetchall()
        assert len(policies) == 2
        assert all(p["relrowsecurity"] and p["relforcerowsecurity"] for p in policies)


def test_revision_approval_correction_revocation_and_immutability(database):
    tenant, owner = "nyameko", _subject()
    with db.connection(database) as conn:
        conversation_id, message_id = _source(conn, tenant, owner)
        memory_id = _candidate(conn, tenant, owner, conversation_id, message_id)
        with db.scoped(conn, tenant, owner):
            with pytest.raises(psycopg.Error):
                with conn.transaction():
                    conn.execute(
                        "UPDATE acp1.memory_revision SET body='tampered' WHERE memory_id=%s",
                        (memory_id,),
                    )
            with pytest.raises(psycopg.Error):
                with conn.transaction():
                    conn.execute(
                        "UPDATE acp1.memory_item "
                        "SET status='active',approved_at=now() WHERE id=%s",
                        (memory_id,),
                    )
        _transition(conn, tenant, owner, memory_id, 2, "approved", "Remember test")
        _transition(conn, tenant, owner, memory_id, 3, "corrected", "Corrected test")
        _transition(conn, tenant, owner, memory_id, 4, "revoked", None)
        with db.scoped(conn, tenant, owner):
            item = conn.execute(
                "SELECT status,current_revision FROM acp1.memory_item WHERE id=%s",
                (memory_id,),
            ).fetchone()
            assert item == {"status": "revoked", "current_revision": 4}
            events = conn.execute(
                "SELECT revision,event_type,body FROM acp1.memory_revision "
                "WHERE memory_id=%s ORDER BY revision",
                (memory_id,),
            ).fetchall()
            assert [event["event_type"] for event in events] == [
                "candidate_created", "approved", "corrected", "revoked"
            ]
            assert events[2]["body"] == "Corrected test"
            assert events[3]["body"] is None
            with pytest.raises(psycopg.Error):
                with conn.transaction():
                    conn.execute(
                        "UPDATE acp1.memory_item "
                        "SET status='active',current_revision=5 WHERE id=%s",
                        (memory_id,),
                    )


def test_source_must_be_owner_user_authored_message(database):
    tenant, owner = "nyameko", _subject()
    with db.connection(database) as conn:
        conversation_id, message_id = _source(
            conn, tenant, owner, author_kind="assistant"
        )
        with pytest.raises(psycopg.Error):
            _candidate(conn, tenant, owner, conversation_id, message_id)
