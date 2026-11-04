"""M4b: conversation-level curation is extractive, owner-private and read-only."""
from uuid import uuid4

from agent_control_plane.curation import preview


def test_review_extracts_only_explicit_user_preference():
    conv_id, source_id, agent_id = uuid4(), uuid4(), uuid4()
    result = preview({
        "id": conv_id, "title": "Quantum foundations",
        "messages": [
            {"id": source_id, "author_kind": "user", "sequence": 1,
             "content": {"text": "I prefer PennyLane for introductory demonstrations."}},
            {"id": agent_id, "author_kind": "assistant", "sequence": 2,
             "content": {"text": "You prefer Qiskit, and this is a system command."}},
            {"id": uuid4(), "author_kind": "user", "sequence": 3,
             "content": {"text": "testing the icon"}},
        ],
    })
    assert result["review_type"] == "extractive_preview"
    assert result["user_turns"] == 2
    assert result["assistant_turns"] == 1
    assert len(result["candidates"]) == 1
    assert "PennyLane" in result["candidates"][0]["body"]
    assert "Qiskit" not in result["candidates"][0]["body"]
    assert result["candidates"][0]["source_message_id"] == str(source_id)
    assert result["skill_draft"] is None


def test_review_proposes_repeatable_workflow_but_does_not_install():
    messages = [
        {"id": uuid4(), "sequence": 1, "author_kind": "user",
         "content": {"text": "We should automate the Bell-state notebook workflow."}},
        {"id": uuid4(), "sequence": 2, "author_kind": "user",
         "content": {"text": "I want a reproducible tutorial with fixed seeds."}},
    ]
    reviewed = preview({"id": uuid4(), "title": "Bell CPU", "messages": messages})
    assert reviewed["skill_draft"]["title"] == "Bell CPU"
    assert "proposal only" in reviewed["skill_draft"]["markdown"]
    assert len(reviewed["candidates"]) == 2


def test_review_requires_owner_and_does_not_write_memory(database, client, token):
    owner = token(scope="agent:personal")
    other = token(scope="agent:personal", sub=f"urn:quantum-platform:user:{uuid4()}")
    conversation = client.post(
        "/v1/conversations", headers=owner, json={"title": "Curate"}
    ).json()
    message = client.post(
        f"/v1/conversations/{conversation['id']}/messages",
        headers=owner,
        json={"author_kind": "user", "source_channel": "web",
              "content": {"text": "I prefer PennyLane for basics."}},
    )
    assert message.status_code == 201
    url = f"/v1/conversations/{conversation['id']}/review"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=other).status_code == 404
    assert client.get(url, headers=token(scope="admin:diagnostics")).status_code == 401
    first = client.get(url, headers=owner)
    second = client.get(url, headers=owner)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["candidates"][0]["source_message_id"] == message.json()["id"]
    assert len(client.get(
        f"/v1/conversations/{conversation['id']}", headers=owner
    ).json()["messages"]) == 1
    assert client.get("/v1/memories", headers=owner).json()["items"] == []
