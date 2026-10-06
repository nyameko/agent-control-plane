from uuid import uuid4

from agent_control_plane import db
from agent_control_plane.auth import Principal


def test_personal_conversation_persists_across_requests_and_is_subject_isolated(
    database, client, token
):
    owner_headers = token(scope="agent:personal")
    project = client.post(
        "/v1/projects", headers=owner_headers, json={"title": "M4 Persistence Test"}
    )
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]

    conversation = client.post(
        "/v1/conversations",
        headers=owner_headers,
        json={"title": "Persistence Drill", "project_id": project_id},
    )
    assert conversation.status_code == 201, conversation.text
    conversation_id = conversation.json()["id"]

    marker = {"text": "Remember ACP-PERSIST-7F31"}
    message = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        headers=owner_headers,
        json={
            "author_kind": "user",
            "content": marker,
            "source_channel": "web",
            "client_message_id": "browser-turn-1",
        },
    )
    assert message.status_code == 201, message.text
    assert message.json()["sequence"] == 1

    reopened = client.get(f"/v1/conversations/{conversation_id}", headers=owner_headers)
    assert reopened.status_code == 200
    assert reopened.json()["project_id"] == project_id
    assert reopened.json()["messages"][0]["content"] == marker

    other_subject = f"urn:quantum-platform:user:{uuid4()}"
    other_headers = token(scope="agent:personal", sub=other_subject)
    forbidden = client.get(
        f"/v1/conversations/{conversation_id}",
        headers=other_headers,
    )
    assert forbidden.status_code == 404
    assert client.get("/v1/conversations", headers=other_headers).json()["items"] == []
    assert client.get("/v1/projects", headers=other_headers).json()["items"] == []


def test_message_client_id_is_idempotent(database, client, token):
    headers = token(scope="agent:personal")
    conversation_id = client.post(
        "/v1/conversations", headers=headers, json={"title": "Persistence Drill"}
    ).json()["id"]
    body = {
        "author_kind": "user",
        "content": "same turn",
        "source_channel": "jupyter",
        "client_message_id": "jupyter-42",
    }
    first = client.post(
        f"/v1/conversations/{conversation_id}/messages", headers=headers, json=body
    )
    second = client.post(
        f"/v1/conversations/{conversation_id}/messages", headers=headers, json=body
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    detail = client.get(f"/v1/conversations/{conversation_id}", headers=headers).json()
    assert len(detail["messages"]) == 1


def test_personal_rls_requires_subject_context(database):
    owner = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
    outsider = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
    with db.connection(database) as conn:
        project = db.create_project(conn, owner, "M4 Persistence Test")
        conversation = db.create_conversation(
            conn, owner, "Persistence Drill", project_id=project["id"]
        )
        db.append_message(
            conn,
            owner,
            conversation["id"],
            author_kind="user",
            content={"text": "ACP-PERSIST-7F31"},
            source_channel="ssh",
        )
        assert db.conversation_detail(conn, outsider, conversation["id"]) is None
        with db.scoped(conn, owner.tenant):
            rows = conn.execute("SELECT count(*) AS n FROM acp1.conversation").fetchone()
            assert rows["n"] == 0


def test_personal_scope_does_not_authorize_admin_api(database, client, token):
    headers = token(scope="agent:personal")
    assert client.get("/v1/admin/tasks", headers=headers).status_code == 401


def test_admin_scope_does_not_authorize_personal_api(database, client, token):
    assert client.get("/v1/conversations", headers=token()).status_code == 401


def test_schema_is_migrated_to_m4a(database):
    with db.connection(database) as conn:
        versions = conn.execute(
            "SELECT version FROM acp1.schema_version ORDER BY version"
        ).fetchall()
        assert versions == [{"version": 1}, {"version": 2}, {"version": 3}]
        db.ready(conn)
