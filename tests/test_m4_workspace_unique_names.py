"""Canonical ACP workspace names: unique within one user's active workspace.

Legacy duplicate names remain stored until owner archives or renames them.
This is an additive application-level rule, not a destructive migration.
"""

from uuid import uuid4


def version(row):
    return '"' + row["updated_at"] + '"'


def test_empty_chats_get_distinct_names_and_can_retain_empty_messages(database, client, token):
    owner = token(scope="agent:personal")
    created = [
        client.post("/v1/conversations", headers=owner, json={"title": "New chat"})
        for _ in range(3)
    ]
    assert all(response.status_code == 201 for response in created)
    rows = [response.json() for response in created]
    assert [row["title"] for row in rows] == ["New chat", "New chat (2)", "New chat (3)"]
    assert len({row["id"] for row in rows}) == 3
    assert client.get(f"/v1/conversations/{rows[1]['id']}", headers=owner).json()[
        "messages"
    ] == []


def test_duplicate_custom_titles_rejected_without_cross_subject_leak(database, client, token):
    owner = token(scope="agent:personal")
    other = token(scope="agent:personal", sub=f"urn:quantum-platform:user:{uuid4()}")
    first = client.post("/v1/conversations", headers=owner, json={"title": "Bell notes"})
    assert first.status_code == 201
    collision = client.post("/v1/conversations", headers=owner, json={"title": "  bELL notes "})
    assert collision.status_code == 409
    assert client.post(
        "/v1/conversations", headers=other, json={"title": "Bell notes"}
    ).status_code == 201
    original = first.json()
    archived = client.patch(
        f"/v1/conversations/{original['id']}",
        headers={**owner, "If-Match": version(original)},
        json={"archived": True},
    )
    assert archived.status_code == 200, archived.text
    second = client.post("/v1/conversations", headers=owner, json={"title": "Bell notes"})
    assert second.status_code == 201, second.text
    restore = client.patch(
        f"/v1/conversations/{original['id']}",
        headers={**owner, "If-Match": version(archived.json())},
        json={"archived": False},
    )
    assert restore.status_code == 409


def test_duplicate_project_rename_rejected_and_archive_preserved(database, client, token):
    owner = token(scope="agent:personal")
    p1 = client.post("/v1/projects", headers=owner, json={"title": "Photonics"})
    p2 = client.post("/v1/projects", headers=owner, json={"title": "Bell"})
    assert p1.status_code == p2.status_code == 201
    assert client.post("/v1/projects", headers=owner, json={
        "title": " PHOTONICS ",
    }).status_code == 409
    collision = client.patch(
        f"/v1/projects/{p2.json()['id']}",
        headers={**owner, "If-Match": version(p2.json())},
        json={"title": "photonics"},
    )
    assert collision.status_code == 409
    # Existing metadata remains recoverable on a conflict.
    assert client.get(
        f"/v1/projects/{p2.json()['id']}", headers=owner,
    ).json()["title"] == "Bell"
