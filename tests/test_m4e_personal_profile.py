"""M4e: user-owned portable profile contract and runtime reconstruction."""

from uuid import uuid4


def test_profile_is_owner_only_revisioned_and_survives_new_connection(database, client, token):
    owner = token(scope="agent:personal")
    other = token(scope="agent:personal", sub=f"urn:quantum-platform:user:{uuid4()}")
    assert client.get("/v1/profile", headers=owner).json() == {"profile": None}

    payload = {
        "display_name": "Research assistant",
        "instructions": "Prefer mathematical explanations and cite primary sources.",
        "model_route": "reasoning",
    }
    created = client.put(
        "/v1/profile", headers={**owner, "If-Match": '"0"'}, json=payload,
    )
    assert created.status_code == 200, created.text
    profile = created.json()
    assert profile["revision"] == 1
    assert created.headers["etag"] == '"1"'
    assert client.get("/v1/profile", headers=owner).json()["profile"]["id"] == profile["id"]

    # No cross-user read or overwrite.
    assert client.get("/v1/profile", headers=other).json() == {"profile": None}
    assert client.put(
        "/v1/profile", headers={**other, "If-Match": '"1"'}, json=payload,
    ).status_code == 412
    stale = client.put(
        "/v1/profile", headers={**owner, "If-Match": '"0"'}, json=payload,
    )
    assert stale.status_code == 412

    revised = client.put(
        "/v1/profile", headers={**owner, "If-Match": '"1"'},
        json={**payload, "model_route": "general"},
    )
    assert revised.status_code == 200, revised.text
    assert revised.json()["id"] == profile["id"]
    assert revised.json()["revision"] == 2
    # The next authenticated API read uses a fresh database connection.
    assert client.get("/v1/profile", headers=owner).json()["profile"]["model_route"] == "general"


def test_profile_rejects_unauthorized_and_unbounded_claims(database, client, token):
    base = {"display_name": "Profile", "instructions": "", "model_route": "general"}
    assert client.get("/v1/profile").status_code == 401
    assert client.get("/v1/profile", headers=token(scope="admin:diagnostics")).status_code == 401
    assert client.put(
        "/v1/profile", headers={**token(scope="agent:personal"), "If-Match": '"0"'},
        json={**base, "credentials": "no"},
    ).status_code == 422
    assert client.put(
        "/v1/profile", headers={**token(scope="agent:personal"), "If-Match": '"0"'},
        json={**base, "instructions": "x" * 2001},
    ).status_code == 422
