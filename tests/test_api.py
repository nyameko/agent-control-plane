from fastapi.testclient import TestClient

from agent_control_plane.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "agent-control-plane",
        "version": "0.1.0",
    }


def test_dry_run_rejects_unknown_fields_and_never_executes():
    response = client.post(
        "/v1/plans/dry-run",
        json={
            "subject": "django:user:1",
            "tenant": "nyameko-lab",
            "channel": "web",
            "domain": "infrastructure",
            "intent": "Propose a patch",
            "mutation_requested": True,
        },
    )
    assert response.status_code == 200
    plan = response.json()
    assert plan["approval_required"] is True
    assert plan["execution_class"] == "sandbox-cpu-standard"

    invalid = client.post(
        "/v1/plans/dry-run",
        json={
            "subject": "django:user:1",
            "tenant": "nyameko-lab",
            "channel": "web",
            "domain": "general",
            "intent": "Hello",
            "physical_hostname": "h200-node-01"
        },
    )
    assert invalid.status_code == 422
