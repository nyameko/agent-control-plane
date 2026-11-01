"""M4c C2: signed programme boundary, RLS isolation and canonical group transcript."""

from uuid import uuid4

import jwt


def _claim(token, programme_id, role="researcher", **override):
    return token(
        scope="agent:programme", programme_id=programme_id,
        programme_role=role, **override,
    )


def test_programme_rooms_share_only_with_same_authorized_programme(database, client, token):
    pi = _claim(token, 101, "pi")
    member = _claim(token, 101)
    admin = _claim(token, 101, "admin")
    unrelated = _claim(token, 102, "pi")
    other_user = _claim(
        token, 101, "researcher",
        sub=f"urn:quantum-platform:user:{uuid4()}",
    )

    # Only PI and delegated admin can create a room.
    assert client.post(
        "/v1/programmes/101/conversations",
        headers=member, json={"title": "Unauthorised"},
    ).status_code == 403
    room = client.post(
        "/v1/programmes/101/conversations",
        headers=pi, json={"title": "Shared research discussion"},
    )
    assert room.status_code == 201, room.text
    room_id = room.json()["id"]
    assert len(client.get("/v1/programmes/101/conversations", headers=member).json()["items"]) == 1

    payload = {
        "content": {"text": "What does the CHSH inequality test?"},
        "source_channel": "web", "client_message_id": str(uuid4()),
    }
    path = f"/v1/programmes/101/conversations/{room_id}/messages"
    first = client.post(path, headers=member, json=payload)
    assert first.status_code == 201, first.text
    repeated = client.post(path, headers=member, json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["id"] == first.json()["id"]
    second = client.post(
        path, headers=other_user, json={
            **payload, "client_message_id": str(uuid4()),
            "content": {"text": "I will compare with Qiskit Aer."},
        },
    )
    assert second.status_code == 201, second.text
    assert second.json()["author_subject"] != first.json()["author_subject"]

    detail = client.get(
        f"/v1/programmes/101/conversations/{room_id}", headers=admin,
    )
    assert detail.status_code == 200
    assert [x["sequence"] for x in detail.json()["messages"]] == [1, 2]
    assert detail.json()["messages"][0]["content"] == payload["content"]

    # Separate programme scope never sees another programme's rooms.
    assert client.get(
        f"/v1/programmes/102/conversations/{room_id}", headers=unrelated,
    ).status_code == 404
    assert client.post(
        f"/v1/programmes/102/conversations/{room_id}/messages",
        headers=unrelated,
        json={"content": "Injected", "source_channel": "web"},
    ).status_code == 404
    assert client.get(
        "/v1/programmes/102/conversations", headers=unrelated,
    ).json()["items"] == []
    assert client.get(
        "/v1/programmes/102/conversations", headers=member,
    ).status_code == 404


def test_programme_claims_are_strictly_verified(client, token):
    path = "/v1/programmes/101/conversations"
    assert client.get(path).status_code == 401
    assert client.get(path, headers=token(scope="agent:personal")).status_code == 401
    for claims in (
        {"scope": "agent:programme"},
        {"scope": "agent:programme", "programme_id": True, "programme_role": "pi"},
        {"scope": "agent:programme", "programme_id": -1, "programme_role": "pi"},
        {"scope": "agent:programme", "programme_id": "101", "programme_role": "pi"},
        {"scope": "agent:programme", "programme_id": 101, "programme_role": "owner"},
        {"scope": "agent:personal agent:programme", "programme_id": 101, "programme_role": "pi"},
        {"scope": "agent:personal", "programme_id": 101, "programme_role": "pi"},
    ):
        assert client.get(path, headers=token(**claims)).status_code == 401


def test_programme_routing_rejects_extra_fields_and_denies_private_memory(client, token):
    programme = _claim(token, 101, "pi")
    assert client.post(
        "/v1/programmes/101/conversations",
        headers=programme,
        json={"title": "Valid", "owner_subject": "forged"},
    ).status_code == 422
    assert client.get("/v1/memories", headers=programme).status_code == 401
    assert client.get("/v1/projects", headers=programme).status_code == 401
