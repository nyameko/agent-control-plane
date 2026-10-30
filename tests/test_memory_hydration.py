"""M4b opt-in memory context for a fresh conversation and ephemeral Hermes."""
from uuid import uuid4
from types import SimpleNamespace

from agent_control_plane import db
from agent_control_plane.auth import Principal
from agent_control_plane.personal_worker import run_once


def test_approved_memory_cross_conversation_and_revocation(database, client, token, config):
    headers = token(scope="agent:personal")
    owner = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
    with db.connection(database) as conn:
        c1 = db.create_conversation(conn, owner, "Original research")
        first = db.append_message(
            conn, owner, c1["id"], author_kind="user",
            content={"text": "Prefer Qiskit for demos."}, source_channel="web",
        )
        conn.execute("SELECT 1")
        with db.scoped(conn, owner.tenant, owner.subject):
            memory_id = uuid4()
            conn.execute(
                "INSERT INTO acp1.memory_item "
                "(id,tenant,owner_subject,creation_key,creation_payload_sha256,kind,"
                "source_conversation_id,source_message_id,source_sha256) "
                "VALUES (%s,%s,%s,%s,%s,'preference',%s,%s,%s)",
                (
                    memory_id, owner.tenant, owner.subject, uuid4(), "a"*64,
                    c1["id"], first["id"], "b"*64,
                ),
            )
            conn.execute(
                "INSERT INTO acp1.memory_revision "
                "(memory_id,tenant,owner_subject,revision,event_type,body,actor_subject)"
                " VALUES (%s,%s,%s,1,'candidate_created',%s,%s)",
                (memory_id, owner.tenant, owner.subject, "Prefer Qiskit.", owner.subject),
            )
            conn.execute(
                "INSERT INTO acp1.memory_revision "
                "(memory_id,tenant,owner_subject,revision,event_type,body,actor_subject)"
                " VALUES (%s,%s,%s,2,'approved',%s,%s)",
                (memory_id, owner.tenant, owner.subject, "Prefer Qiskit.", owner.subject),
            )
            conn.execute(
                "UPDATE acp1.memory_item SET status='active',approved_at=now(),"
                "current_revision=2 WHERE id=%s", (memory_id,),
            )
        c2 = db.create_conversation(conn, owner, "Second research session")
        row, _ = db.create_turn(
            conn, owner, c2["id"], key=uuid4(), content="What should I use?",
            source_channel="web",
        )
        # Fresh run reconstruction should not depend on a previous Hermes profile.
        seen = {}
        def responder(conn, settings, run, context):
            seen["context"] = context
            return "I can help with Qiskit."
        config_enabled = SimpleNamespace(
            **{**vars(config), "personal_memory_enabled": True}
        )
        assert run_once(conn, config_enabled, responder=responder)
        assert len(seen["context"]["messages"]) == 1
        assert seen["context"]["memories"][0]["body"] == "Prefer Qiskit."
        assert seen["context"]["memories"][0]["source_message_id"] == first["id"]
        assert seen["context"]["conversation"]["id"] == c2["id"]
        assert row is not None
        with db.scoped(conn, owner.tenant, owner.subject):
            conn.execute(
                "INSERT INTO acp1.memory_revision "
                "(memory_id,tenant,owner_subject,revision,event_type,body,actor_subject)"
                " VALUES (%s,%s,%s,3,'revoked',NULL,%s)",
                (memory_id, owner.tenant, owner.subject),
            )
            conn.execute(
                "UPDATE acp1.memory_item SET status='revoked',revoked_at=now(),"
                "current_revision=3 WHERE id=%s", (memory_id,),
            )
        c3 = db.create_conversation(conn, owner, "Third research session")
        db.create_turn(
            conn, owner, c3["id"], key=uuid4(), content="Do you remember?",
            source_channel="web",
        )
        assert run_once(conn, config_enabled, responder=responder)
        assert seen["context"]["memories"] == []
        with db.scoped(conn, owner.tenant, owner.subject):
            assert conn.execute(
                "SELECT count(*) AS n FROM acp1.memory_item WHERE id=%s",
                (memory_id,),
            ).fetchone()["n"] == 1
        other = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
        c4 = db.create_conversation(conn, other, "Isolated session")
        db.create_turn(
            conn, other, c4["id"], key=uuid4(), content="Recall another user?",
            source_channel="web",
        )
        assert run_once(conn, config_enabled, responder=responder)
        assert seen["context"]["memories"] == []


def test_memory_disabled_preserves_m4a_behavior(database, config):
    principal = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
    with db.connection(database) as conn:
        conversation = db.create_conversation(conn, principal, "M4a fallback")
        db.create_turn(
            conn, principal, conversation["id"], key=uuid4(), content="Hello",
            source_channel="api",
        )
        seen = {}
        def responder(conn, settings, run, context):
            seen.update(context)
            return "Hello."
        assert run_once(conn, config, responder=responder)
        assert "memories" not in seen
