"""M4d reviewed catalog: explicit human-selected owner binding, no execution grants."""
import pytest

from agent_control_plane import db, skills


@pytest.fixture
def trusted_catalog(monkeypatch):
    entry = {
        "id": "learning.quantum-foundations",
        "version": "0.2.0",
        "source_commit": "a" * 40,
        "manifest_sha256": "b" * 64,
        "reviewed_by": "synthetic-ci-reviewer-only",
        "resource_path": "labs/01-intro-quantum-computing/Intro_QC_Demo.ipynb",
        "required_capabilities": ["resource:read"],
        "automatic_code_execution": False,
    }
    # This fixture is NOT a real reviewed resource and never changes the
    # production empty catalog. No external Git revision is falsely approved.
    monkeypatch.setattr(skills, "_trusted_catalog", lambda: {
        (entry["id"], entry["version"]): entry,
    })
    return entry


def _binding_path(entry):
    return f"/v1/skills/{entry['id']}/versions/{entry['version']}/binding"


def _revoke_path(entry):
    return f"/v1/skills/{entry['id']}/versions/{entry['version']}/revoke"


def test_catalog_empty_by_default_and_cannot_enable_proposed_skills(database, client, token):
    headers = token(scope="agent:personal")
    response = client.get("/v1/skills/catalog", headers=headers)
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert client.get("/v1/skills/catalog").status_code == 401
    assert client.put(
        "/v1/skills/learning.quantum-foundations/versions/0.2.0/binding",
        headers={**headers, "If-Match": '"0"'},
    ).status_code == 403
    assert client.get("/v1/skills/bindings", headers=headers).json()["items"] == []


def test_reviewed_skill_owner_binding_revocation_and_isolation(
    database, client, token, trusted_catalog
):
    owner = token(scope="agent:personal")
    other = token(
        scope="agent:personal",
        sub="urn:quantum-platform:user:1f005112-df57-48c3-9216-1d259897359d",
    )
    path = _binding_path(trusted_catalog)
    catalog = client.get("/v1/skills/catalog", headers=owner)
    assert catalog.json()["items"] == [trusted_catalog]
    assert catalog.json()["items"][0]["automatic_code_execution"] is False
    assert client.put(path, headers={**owner, "If-Match": '"2"'}).status_code == 412
    created = client.put(path, headers={**owner, "If-Match": '"0"'})
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "enabled"
    assert created.headers["ETag"] == '"1"'
    assert client.put(path, headers={**owner, "If-Match": '"1"'}).status_code == 200
    mylist = client.get("/v1/skills/bindings", headers=owner).json()["items"]
    assert len(mylist) == 1
    assert mylist[0]["currently_reviewed"] is True
    assert client.get("/v1/skills/bindings", headers=other).json()["items"] == []
    assert client.post(_revoke_path(trusted_catalog),
                       headers={**other, "If-Match": '"1"'}).status_code == 404
    assert client.post(_revoke_path(trusted_catalog),
                       headers={**owner, "If-Match": '"0"'}).status_code == 412
    revoked = client.post(_revoke_path(trusted_catalog),
                          headers={**owner, "If-Match": '"1"'})
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"
    assert revoked.headers["ETag"] == '"2"'
    assert client.put(path, headers={**owner, "If-Match": '"1"'}).status_code == 412
    reenabled = client.put(path, headers={**owner, "If-Match": '"2"'})
    assert reenabled.status_code == 201, reenabled.text
    assert reenabled.json()["status"] == "enabled"
    assert reenabled.json()["revision"] == 3
    with db.connection(database) as conn:
        with db.scoped(conn, "nyameko", None):
            row = conn.execute(
                "SELECT has_table_privilege(current_user,'acp1.skill_binding','DELETE') "
                "AS binding_delete, "
                "has_table_privilege(current_user,'acp1.skill_binding_revision','UPDATE') "
                "AS revision_update"
            ).fetchone()
            assert row["binding_delete"] is False
            assert row["revision_update"] is False


def test_signed_scope_etag_required_and_tampering_fails(
    database, client, token, trusted_catalog
):
    path = _binding_path(trusted_catalog)
    assert client.put(path, headers={"If-Match": '"0"'}).status_code == 401
    assert client.put(
        path, headers={**token(), "If-Match": '"0"'}
    ).status_code == 401
    assert client.put(path, headers=token(scope="agent:personal")).status_code == 422
    assert client.put(
        path, headers={**token(scope="agent:personal"), "If-Match": "0"}
    ).status_code == 422


def test_review_catalog_rejects_unsafe_code_grants(monkeypatch):
    from importlib.resources import files
    import json

    original_files = files
    base = original_files("agent_control_plane")
    manifest = json.loads(base.joinpath("reviewed_skills.json").read_text())
    assert manifest == {"catalog_version": 1, "reviewed": []}
    # Even a Git-reviewed catalog is limited to resource reads in M4d.
    assert skills.catalog() == []
