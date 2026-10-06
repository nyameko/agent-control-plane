from uuid import uuid4

from agent_control_plane import db
from agent_control_plane.auth import Principal
from agent_control_plane.personal_worker import run_once as run_personal_once


def _conversation(client, headers):
    project = client.post(
        "/v1/projects",
        headers=headers,
        json={"title": "M4 Persistence Test"},
    ).json()
    conversation = client.post(
        "/v1/conversations",
        headers=headers,
        json={"title": "Persistence Drill", "project_id": project["id"]},
    ).json()
    return project, conversation


def test_turn_is_atomic_idempotent_and_returns_run(database, client, token):
    headers = token(scope="agent:personal")
    _, conversation = _conversation(client, headers)
    key = str(uuid4())
    body = {
        "content": {"text": "ACP-PERSIST-7F31"},
        "source_channel": "web",
        "client_message_id": "m4a-turn-1",
    }
    first = client.post(
        f"/v1/conversations/{conversation['id']}/turns",
        headers={**headers, "Idempotency-Key": key},
        json=body,
    )
    assert first.status_code == 202, first.text
    second = client.post(
        f"/v1/conversations/{conversation['id']}/turns",
        headers={**headers, "Idempotency-Key": key},
        json=body,
    )
    assert second.status_code == 200
    assert second.json()["task_id"] == first.json()["task_id"]
    assert second.json()["run_id"] == first.json()["run_id"]

    run = client.get(f"/v1/runs/{first.json()['run_id']}", headers=headers)
    assert run.status_code == 200
    assert run.json()["status"] == "queued"

    detail = client.get(
        f"/v1/conversations/{conversation['id']}",
        headers=headers,
    ).json()
    assert [message["content"] for message in detail["messages"]] == [
        {"text": "ACP-PERSIST-7F31"}
    ]


def test_personal_worker_hydrates_canonical_history_and_commits_response(
    database, client, token, config
):
    headers = token(scope="agent:personal")
    project, conversation = _conversation(client, headers)
    key = str(uuid4())
    created = client.post(
        f"/v1/conversations/{conversation['id']}/turns",
        headers={**headers, "Idempotency-Key": key},
        json={
            "content": {"text": "Remember ACP-PERSIST-7F31"},
            "source_channel": "web",
            "client_message_id": "persistence-marker",
        },
    )
    run_id = created.json()["run_id"]

    seen = {}

    def responder(conn, settings, run, context):
        seen["project_id"] = context["conversation"]["project_id"]
        seen["messages"] = context["messages"]
        return "You gave me the marker ACP-PERSIST-7F31."

    with db.connection(database) as conn:
        assert run_personal_once(conn, config, responder=responder)

    assert str(seen["project_id"]) == project["id"]
    assert seen["messages"][-1]["content"] == {"text": "Remember ACP-PERSIST-7F31"}

    run = client.get(f"/v1/runs/{run_id}", headers=headers).json()
    assert run["status"] == "succeeded"
    assert run["summary"] == "You gave me the marker ACP-PERSIST-7F31."

    detail = client.get(
        f"/v1/conversations/{conversation['id']}",
        headers=headers,
    ).json()
    assert [message["author_kind"] for message in detail["messages"]] == [
        "user",
        "assistant",
    ]
    assert detail["messages"][-1]["content"] == {
        "text": "You gave me the marker ACP-PERSIST-7F31."
    }


def test_personal_and_admin_workers_do_not_claim_each_others_runs(
    database, config
):
    personal = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
    admin = Principal(f"urn:quantum-platform:user:{uuid4()}", "nyameko")
    with db.connection(database) as conn:
        conversation = db.create_conversation(conn, personal, "Persistence Drill")
        db.create_turn(
            conn,
            personal,
            conversation["id"],
            key=uuid4(),
            content="personal",
            source_channel="api",
            client_message_id="personal-1",
        )
        db.create_task(conn, admin, uuid4())

        admin_run = db.claim(conn, config, "test-admin")
        assert admin_run is not None
        personal_run = db.claim_personal(conn, config, "test-personal")
        assert personal_run is not None
        assert admin_run["task_id"] != personal_run["task_id"]


def test_second_user_cannot_read_personal_run(database, client, token):
    owner_headers = token(scope="agent:personal")
    _, conversation = _conversation(client, owner_headers)
    created = client.post(
        f"/v1/conversations/{conversation['id']}/turns",
        headers={**owner_headers, "Idempotency-Key": str(uuid4())},
        json={"content": "private", "source_channel": "web"},
    )
    other_headers = token(
        scope="agent:personal",
        sub=f"urn:quantum-platform:user:{uuid4()}",
    )
    assert client.get(
        f"/v1/runs/{created.json()['run_id']}",
        headers=other_headers,
    ).status_code == 404


def test_interrupted_personal_run_is_terminal_but_history_survives(
    database, client, token, config
):
    headers = token(scope="agent:personal")
    _, conversation = _conversation(client, headers)
    created = client.post(
        f"/v1/conversations/{conversation['id']}/turns",
        headers={**headers, "Idempotency-Key": str(uuid4())},
        json={"content": "survive worker loss", "source_channel": "ssh"},
    )
    with db.connection(database) as conn:
        claimed = db.claim_personal(conn, config, "test")
        assert claimed
    with db.connection(database) as conn:
        db.recover_interrupted_personal(conn, "nyameko")

    run = client.get(f"/v1/runs/{created.json()['run_id']}", headers=headers).json()
    assert run["status"] == "failed"
    assert run["failure_code"] == "worker_interrupted"
    detail = client.get(
        f"/v1/conversations/{conversation['id']}",
        headers=headers,
    ).json()
    assert detail["messages"][0]["content"] == "survive worker loss"
