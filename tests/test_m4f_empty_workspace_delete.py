"""M4f: permanent deletion only for genuinely empty private ACP workspaces.

This test suite uses the isolated PostgreSQL test DSNs from conftest.py.
It must NEVER run with production ACP_DATABASE_URL as a test DSN.
"""
from uuid import uuid4


def etag(item):
    return '"' + item["updated_at"] + '"'


def test_owner_can_delete_empty_chat_and_project_after_explicit_cas(database, client, token):
    owner = token(scope="agent:personal")
    project = client.post("/v1/projects", headers=owner, json={"title": "Empty scratch"}).json()
    conv = client.post(
        "/v1/conversations",
        headers=owner,
        json={"title": "New chat", "project_id": project["id"]},
    ).json()
    conversation_url = "/v1/conversations/" + conv["id"]
    project_url = "/v1/projects/" + project["id"]

    # Project deletion is blocked while a chat exists, even when the chat is empty.
    blocked = client.delete(project_url, headers={**owner, "If-Match": etag(project)})
    assert blocked.status_code == 409, blocked.text
    assert client.get(project_url, headers=owner).status_code == 200

    deleted = client.delete(conversation_url, headers={**owner, "If-Match": etag(conv)})
    assert deleted.status_code == 204, deleted.text
    assert deleted.content == b""
    assert client.get(conversation_url, headers=owner).status_code == 404
    assert all(
        chat["id"] != conv["id"]
        for chat in client.get("/v1/conversations", headers=owner).json()["items"]
    )
    deleted_project = client.delete(project_url, headers={**owner, "If-Match": etag(project)})
    assert deleted_project.status_code == 204, deleted_project.text
    assert client.get(project_url, headers=owner).status_code == 404


def test_nonempty_chat_and_archived_project_are_protected(database, client, token):
    owner = token(scope="agent:personal")
    project = client.post("/v1/projects", headers=owner, json={"title": "Research"}).json()
    conv = client.post(
        "/v1/conversations", headers=owner,
        json={"title": "Bell measurements", "project_id": project["id"]},
    ).json()
    chat_url = "/v1/conversations/" + conv["id"]
    project_url = "/v1/projects/" + project["id"]
    message = client.post(
        chat_url + "/messages",
        headers=owner,
        json={"author_kind": "user", "content": {"text": "Keep this"},
              "source_channel": "web"},
    )
    assert message.status_code == 201
    fresh = client.get(chat_url, headers=owner).json()
    blocked = client.delete(chat_url, headers={**owner, "If-Match": etag(fresh)})
    assert blocked.status_code == 409, blocked.text
    assert client.get(chat_url, headers=owner).json()["messages"][0]["id"] == message.json()["id"]

    # An archived conversation still blocks deletion of its parent project.
    archived = client.patch(
        chat_url, headers={**owner, "If-Match": etag(fresh)}, json={"archived": True},
    )
    assert archived.status_code == 200, archived.text
    fresh_project = client.get(project_url, headers=owner).json()
    blocked = client.delete(project_url, headers={**owner, "If-Match": etag(fresh_project)})
    assert blocked.status_code == 409, blocked.text


def test_empty_workspace_delete_is_owner_only_and_stale_safe(database, client, token):
    owner = token(scope="agent:personal")
    outsider = token(scope="agent:personal", sub=f"urn:quantum-platform:user:{uuid4()}")
    diag = token(scope="admin:diagnostics")
    conv = client.post("/v1/conversations", headers=owner, json={"title": "Disposable"}).json()
    project = client.post(
        "/v1/projects", headers=owner, json={"title": "Disposable project"},
    ).json()
    for url, row in (
        ("/v1/conversations/" + conv["id"], conv),
        ("/v1/projects/" + project["id"], project),
    ):
        assert client.delete(url, headers={"If-Match": etag(row)}).status_code == 401
        assert client.delete(url, headers={**diag, "If-Match": etag(row)}).status_code == 401
        assert client.delete(url, headers={**outsider, "If-Match": etag(row)}).status_code == 404
        assert client.delete(url, headers=owner).status_code == 422
        assert client.delete(url, headers={**owner, "If-Match": '"stale"'}).status_code == 412
        assert client.get(url, headers=owner).status_code == 200

    deleted = client.delete(
        "/v1/conversations/" + conv["id"], headers={**owner, "If-Match": etag(conv)},
    )
    assert deleted.status_code == 204
    # Explicit request is idempotently missing, but cannot delete another record.
    assert client.delete(
        "/v1/conversations/" + conv["id"], headers={**owner, "If-Match": etag(conv)},
    ).status_code == 404


def test_empty_chat_protected_after_run_task_is_recorded(database, client, token):
    owner = token(scope="agent:personal")
    conv = client.post("/v1/conversations", headers=owner, json={"title": "Keep run"}).json()
    url = "/v1/conversations/" + conv["id"]
    accepted = client.post(
        url + "/turns",
        headers={**owner, "Idempotency-Key": str(uuid4())},
        json={"content": {"text": "Check"}, "source_channel": "web",
              "client_message_id": str(uuid4())},
    )
    assert accepted.status_code == 202, accepted.text
    # Run/turn creation requires a persisted message and task.
    latest = client.get(url, headers=owner).json()
    assert client.delete(url, headers={**owner, "If-Match": etag(latest)}).status_code == 409
