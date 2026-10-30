"""PostgreSQL-backed M4b schema and isolation conformance.

This fixture migrates a disposable CI database; never point it at a live database.
"""
from uuid import uuid4

import psycopg
import pytest

from agent_control_plane import db


def create_source(conn, tenant, owner):
    with db.scoped(conn, tenant, owner):
        c = uuid4()
        m = uuid4()
        conn.execute(
            "INSERT INTO acp1.conversation(id,tenant,owner_subject,title)"
            " VALUES (%s,%s,%s,'Memory test')", (c,tenant,owner)
        )
        conn.execute(
            "INSERT INTO acp1.message(id,tenant,owner_subject,conversation_id,"
            "sequence,author_kind,content,source_channel)"
            " VALUES (%s,%s,%s,%s,1,'user','{}'::jsonb,'api')",
            (m,tenant,owner,c)
        )
        return c,m


def candidate(conn, tenant, owner, conversation, message):
    memory = uuid4()
    with db.scoped(conn, tenant, owner):
        conn.execute(
            "INSERT INTO acp1.memory_item(id,tenant,owner_subject,creation_key,"
            "creation_payload_sha256,kind,source_conversation_id,source_message_id,"
            "source_sha256) VALUES (%s,%s,%s,%s,%s,'preference',%s,%s,%s)",
            (memory,tenant,owner,uuid4(),"a"*64,conversation,message,"b"*64)
        )
        conn.execute(
            "INSERT INTO acp1.memory_revision(memory_id,tenant,owner_subject,"
            "revision,event_type,body,actor_subject)"
            " VALUES (%s,%s,%s,1,'candidate_created','Remember test',%s)",
            (memory,tenant,owner,owner)
        )
    return memory


def test_schema_v4_migrated_and_rls_subject_isolated(database):
    owner = f"urn:quantum-platform:user:{uuid4()}"
    other = f"urn:quantum-platform:user:{uuid4()}"
    tenant="nyameko"
    with db.connection(database) as conn:
        db.ready(conn)
        conversation,message = create_source(conn,tenant,owner)
        memory = candidate(conn,tenant,owner,conversation,message)
        with db.scoped(conn,tenant,other):
            assert conn.execute("SELECT count(*) AS n FROM acp1.memory_item").fetchone()["n"] == 0
            assert conn.execute("SELECT count(*) AS n FROM acp1.memory_revision").fetchone()["n"] == 0
            assert conn.execute("UPDATE acp1.memory_item SET status='revoked' WHERE id=%s RETURNING id",(memory,)).fetchone() is None
        with db.scoped(conn,tenant,owner):
            assert conn.execute("SELECT count(*) AS n FROM acp1.memory_item").fetchone()["n"] == 1
            assert conn.execute("SELECT count(*) AS n FROM acp1.memory_revision").fetchone()["n"] == 1


def test_revision_guard_approval_and_revocation(database):
    owner=f"urn:quantum-platform:user:{uuid4()}"
    with db.connection(database) as conn:
        c,m=create_source(conn,"nyameko",owner)
        mid=candidate(conn,"nyameko",owner,c,m)
        with db.scoped(conn,"nyameko",owner):
            with pytest.raises(psycopg.Error):
                with conn.transaction():
                    conn.execute("UPDATE acp1.memory_revision SET body='tampered' WHERE memory_id=%s",(mid,))
            with pytest.raises(psycopg.Error):
                with conn.transaction():
                    conn.execute("UPDATE acp1.memory_item SET status='active',approved_at=now() WHERE id=%s",(mid,))
            conn.execute(
                "INSERT INTO acp1.memory_revision(memory_id,tenant,owner_subject,revision,"
                "event_type,body,actor_subject) VALUES (%s,'nyameko',%s,2,'approved','Remember test',%s)",
                (mid,owner,owner)
            )
            conn.execute("UPDATE acp1.memory_item SET status='active',approved_at=now(),current_revision=2 WHERE id=%s",(mid,))
            conn.execute(
                "INSERT INTO acp1.memory_revision(memory_id,tenant,owner_subject,revision,"
                "event_type,body,actor_subject) VALUES (%s,'nyameko',%s,3,'revoked',NULL,%s)",
                (mid,owner,owner)
            )
            conn.execute("UPDATE acp1.memory_item SET status='revoked',revoked_at=now(),current_revision=3 WHERE id=%s",(mid,))
            assert conn.execute("SELECT status FROM acp1.memory_item WHERE id=%s",(mid,)).fetchone()["status"]=="revoked"
