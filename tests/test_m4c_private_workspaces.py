"""M4c C1: workspace CRUD stays private and never destroys canonical history."""

from uuid import uuid4


def _private_pair(client, headers):
    first = client.post("/v1/projects", headers=headers, json={"title": "One"})
    second = client.post("/v1/projects", headers=headers, json={"title": "Two"})
    assert first.status_code == second.status_code == 201
    conversation = client.post(
        "/v1/conversations",
        headers=headers,
        json={"title": "Bell notes", "project_id": first.json()["id"]},
    )
    assert conversation.status_code == 201
    return first.json(), second.json(), conversation.json()


def _version(payload):
    return '"' + payload["updated_at"] + '"'


def test_private_project_and_conversation_lifecycle_preserves_history(
    database, client, token
):
    headers = token(scope="agent:personal")
    first, second, chat = _private_pair(client, headers)
    message = client.post(
        f"/v1/conversations/{chat['id']}/messages",
        headers=headers,
        json={
            "author_kind": "user",
            "content": {"text": "Bell source"},
            "source_channel": "web",
        },
    )
    assert message.status_code == 201
    renamed = client.patch(
        f"/v1/projects/{first['id']}",
        headers={**headers, "If-Match": _version(first)},
        json={"title": "Research notes"},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["id"] == first["id"]
    assert renamed.json()["title"] == "Research notes"
    assert renamed.headers["ETag"] == _version(renamed.json())
    stale = client.patch(
        f"/v1/projects/{first['id']}",
        headers={**headers, "If-Match": _version(first)},
        json={"title": "Lost update"},
    )
    assert stale.status_code == 412
    moved = client.patch(
        f"/v1/conversations/{chat['id']}",
        headers={**headers, "If-Match": _version(chat)},
        json={"project_id": second["id"], "title": "Bell experiments"},
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["id"] == chat["id"]
    assert moved.json()["project_id"] == second["id"]
    detail = client.get(f"/v1/conversations/{chat['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["messages"][0]["content"] == {"text": "Bell source"}
    unfiled = client.patch(
        f"/v1/conversations/{chat['id']}",
        headers={**headers, "If-Match": _version(moved.json())},
        json={"project_id": None},
    )
    assert unfiled.status_code == 200
    assert unfiled.json()["project_id"] is None
    archived = client.patch(
        f"/v1/projects/{first['id']}",
        headers={**headers, "If-Match": _version(renamed.json())},
        json={"archived": True},
    )
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None
    assert client.get(f"/v1/conversations/{chat['id']}", headers=headers).status_code == 200


def test_private_workspace_mutations_fail_closed(database, client, token):
    headers = token(scope="agent:personal")
    first, second, chat = _private_pair(client, headers)
    other = token(scope="agent:personal", sub=f"urn:quantum-platform:user:{uuid4()}")
    for path, version in [
        (f"/v1/projects/{first['id']}", _version(first)),
        (f"/v1/conversations/{chat['id']}", _version(chat)),
    ]:
        assert client.patch(
            path, headers={**other, "If-Match": version}, json={"title": "Other"}
        ).status_code == 404
        assert client.patch(
            path, headers={**headers, "If-Match": version}, json={}
        ).status_code == 422
    assert client.get(f"/v1/projects/{first['id']}", headers=other).status_code == 404
    assert client.patch(
        f"/v1/conversations/{chat['id']}",
        headers={**headers, "If-Match": _version(chat)},
        json={"project_id": str(uuid4())},
    ).status_code == 404
    assert client.get(f"/v1/projects/{first['id']}", headers=headers).status_code == 200
    assert second["id"] != first["id"]


def test_private_workspaces_require_signed_personal_scope(database, client, token):
    assert client.get("/v1/projects/" + str(uuid4())).status_code == 401
    assert client.patch(
        "/v1/conversations/" + str(uuid4()),
        headers={"If-Match": '"none"'},
        json={"title": "X"},
    ).status_code == 401
