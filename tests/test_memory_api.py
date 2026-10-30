"""Authenticated M4b memory lifecycle on disposable PostgreSQL."""
from uuid import uuid4


def _message(client, headers):
    conversation = client.post(
        "/v1/conversations", headers=headers, json={"title": "Memory API pilot"}
    )
    assert conversation.status_code == 201, conversation.text
    conversation_id = conversation.json()["id"]
    message = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"author_kind": "user", "content": {"text": "Use Qiskit"},
              "source_channel": "web"},
    )
    assert message.status_code == 201, message.text
    return conversation_id, message.json()["id"]


def test_memory_api_approval_retrieval_correction_revocation(database, client, token):
    headers = token(scope="agent:personal")
    conversation_id, message_id = _message(client, headers)
    payload = {
        "source_conversation_id": conversation_id, "source_message_id": message_id,
        "kind": "preference", "body": "I prefer Qiskit.",
    }
    key = str(uuid4())
    creation_headers = {**headers, "Idempotency-Key": key}
    first = client.post("/v1/memories/candidates", headers=creation_headers, json=payload)
    assert first.status_code == 201, first.text
    memory_id = first.json()["id"]
    replay = client.post("/v1/memories/candidates", headers=creation_headers, json=payload)
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == memory_id
    changed = client.post(
        "/v1/memories/candidates", headers=creation_headers,
        json={**payload, "body": "Changed"},
    )
    assert changed.status_code == 409

    retrieval = client.get("/v1/memories/retrieve", headers=headers)
    assert retrieval.status_code == 200
    assert retrieval.json()["items"] == []

    approved = client.post(
        f"/v1/memories/{memory_id}/approve",
        headers={**headers, "If-Match": '"1"'},
        json={},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["revision"] == 2
    assert len(client.get("/v1/memories/retrieve", headers=headers).json()["items"]) == 1

    stale = client.patch(
        f"/v1/memories/{memory_id}",
        headers={**headers, "If-Match": '"1"'},
        json={"body": "My current preference"},
    )
    assert stale.status_code == 409
    corrected = client.patch(
        f"/v1/memories/{memory_id}",
        headers={**headers, "If-Match": '"2"'},
        json={"body": "I prefer PennyLane."},
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["revision"] == 3
    items = client.get("/v1/memories/retrieve", headers=headers).json()["items"]
    assert items[0]["body"] == "I prefer PennyLane."

    outsider = token(scope="agent:personal", sub=f"urn:quantum-platform:user:{uuid4()}")
    assert client.get(f"/v1/memories/{memory_id}", headers=outsider).status_code == 404
    assert client.get("/v1/memories/retrieve", headers=outsider).json()["items"] == []
    assert client.post(
        f"/v1/memories/{memory_id}/revoke",
        headers={**outsider, "If-Match": '"3"'}, json={},
    ).status_code == 404

    revoked = client.post(
        f"/v1/memories/{memory_id}/revoke",
        headers={**headers, "If-Match": '"3"'}, json={"reason": "No longer useful"},
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"
    assert client.get("/v1/memories/retrieve", headers=headers).json()["items"] == []


def test_memory_api_requires_user_source_and_signed_scope(database, client, token):
    owner = token(scope="agent:personal")
    conv, message = _message(client, owner)
    outsider = token(scope="agent:personal", sub=f"urn:quantum-platform:user:{uuid4()}")
    payload = {
        "source_conversation_id": conv, "source_message_id": message,
        "kind": "preference", "body": "Remember my experiment.",
    }
    result = client.post(
        "/v1/memories/candidates",
        headers={**outsider, "Idempotency-Key": str(uuid4())}, json=payload,
    )
    assert result.status_code == 404
    assert client.get("/v1/memories", headers=token()).status_code == 401
    assert client.get("/v1/memories", headers={}).status_code == 401


def test_memory_rejects_credentials_and_bad_revision(database, client, token):
    headers = token(scope="agent:personal")
    conv, message = _message(client, headers)
    payload = {
        "source_conversation_id": conv, "source_message_id": message,
        "kind": "preference", "body": "sk-" + "A" * 25,
    }
    creation = client.post(
        "/v1/memories/candidates",
        headers={**headers, "Idempotency-Key": str(uuid4())}, json=payload,
    )
    assert creation.status_code == 422, creation.text
