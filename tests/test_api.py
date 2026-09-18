from uuid import uuid4

import pytest


def test_health(client):
    assert client.get("/health").json()["version"] == "0.2.0"


@pytest.mark.parametrize("path", ["/v1/admin/tasks", "/v1/admin/tasks/" + str(uuid4())])
def test_history_requires_authentication(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize(
    "claims",
    [
        {"tenant": "another-tenant"},
        {"scope": "research:chat"},
        {"aud": "another-api"},
        {"iss": "untrusted"},
        {"exp": 1},
        {"sub": "1"},
        {"jti": "bad"},
        {"exp": 9999999999},
    ],
)
def test_invalid_claims_rejected(client, token, claims):
    assert client.get("/v1/admin/tasks", headers=token(**claims)).status_code == 401


def test_fixed_tool_rejects_query_and_identity_override(client, token):
    for override in [
        {"query": "up"},
        {"tenant": "another"},
        {"namespace": "kube-system"},
        {"model": "unreviewed"},
        {"intent": "run a shell"},
    ]:
        response = client.post(
            "/v1/admin/tasks",
            headers={**token(), "Idempotency-Key": str(uuid4())},
            json={"diagnostic": "quantum-platform-pod-readiness", **override},
        )
        assert response.status_code == 422


def test_dryrun_auth_and_no_execution(client, token):
    body = {
        "subject": "forged",
        "tenant": "nyameko",
        "channel": "web",
        "domain": "infrastructure",
        "intent": "Propose a patch",
        "mutation_requested": True,
    }
    assert client.post("/v1/plans/dry-run", json=body).status_code == 401
    assert client.post("/v1/plans/dry-run", headers=token(), json=body).status_code == 403
