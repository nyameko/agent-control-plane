"""Terminal client stays thin, authenticated and independent from SSH shell setup."""

import io
import json
import sys
from uuid import uuid4

import httpx
import pytest

from agent_control_plane import terminal_client


@pytest.mark.parametrize("url", [
    "http://insecure.example",
    "https://user:pass@acp.example",
    "https://acp.example/path",
    "https://acp.example/?token=leaked",
    "file:///etc/passwd",
])
def test_terminal_disallows_unsafe_targets(url):
    with pytest.raises(ValueError):
        terminal_client.validated_url(url)


def test_terminal_list_forwards_only_broker_token_and_formats(capsys, monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"items": [{"id": "p1", "title": "My project"}]})

    monkeypatch.setattr(sys, "stdin", io.StringIO("short-lived-assertion\n"))
    result = terminal_client.main(
        ["--url", "https://acp.example", "--token-stdin", "projects"],
        client_factory=lambda **kw: httpx.Client(
            transport=httpx.MockTransport(handler), **kw
        ),
    )
    assert result == 0
    assert "p1" in capsys.readouterr().out
    assert calls[0].url.path == "/v1/projects"
    assert calls[0].headers["Authorization"] == "Bearer short-lived-assertion"


def test_terminal_send_is_idempotent_and_does_not_fake_identity(capsys, monkeypatch):
    seen = []
    room = uuid4()

    def handler(request):
        seen.append(request)
        return httpx.Response(202, json={"run_id": str(uuid4())})

    monkeypatch.setattr(sys, "stdin", io.StringIO("issued-token\n"))
    assert terminal_client.main(
        ["--url", "https://acp.example", "--token-stdin", "send", str(room),
         "Explain superposition"],
        client_factory=lambda **kw: httpx.Client(
            transport=httpx.MockTransport(handler), **kw
        ),
    ) == 0
    outgoing = json.loads(seen[0].content)
    assert outgoing["source_channel"] == "ssh"
    assert outgoing["content"]["text"] == "Explain superposition"
    assert "owner_subject" not in outgoing
    assert "tenant" not in outgoing
    assert seen[0].headers["Idempotency-Key"]
    assert "issued-token" not in capsys.readouterr().out


def test_terminal_denies_expired_or_missing_auth(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("expired-token\n"))
    assert terminal_client.main(
        ["--url", "https://acp.example", "--token-stdin", "chats"],
        client_factory=lambda **kw: httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(401, json={"detail": "expired"})
            ), **kw
        ),
    ) == 3
    assert "expired" in capsys.readouterr().err.lower()
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert terminal_client.main(
        ["--url", "https://acp.example", "--token-stdin", "chats"]
    ) == 2



def test_browser_paired_terminal_uses_portal_gateway_not_raw_acp_jwt(capsys):
    calls = []
    identity = str(uuid4())
    proof = "unit-test-proof-secret-only-in-terminal-process"
    code = "AABBCC112233"

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": identity, "verification_code": code,
                "pairing_proof": proof, "expires_in": 300, "poll_interval": 3,
            })
        if request.url.path.endswith("/terminal-pairings/status/"):
            return httpx.Response(200, json={"state": "approved"})
        assert request.url.path == "/api/v1/agent/terminal-gateway/projects/"
        assert request.headers["Authorization"] == "Pairing " + proof
        assert request.headers["X-ACP-Pairing-ID"] == identity
        assert not request.headers["Authorization"].startswith("Bearer ")
        return httpx.Response(200, json={"items": [{"id": "owned", "title": "Private"}]})

    result = terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair", "projects"],
        client_factory=lambda **kw: httpx.Client(
            transport=httpx.MockTransport(handler), **kw
        ),
    )
    assert result == 0
    out = capsys.readouterr()
    assert "owned" in out.out
    assert code in out.err
    assert proof not in out.out and proof not in out.err
    assert len(calls) == 3


def test_browser_paired_send_source_and_revocation_denial(capsys):
    run_id = str(uuid4())
    conversation_id = uuid4()
    identity = str(uuid4())
    proof = "one-time-ram-only-terminal-proof-fixture"
    seen = []

    def handler(request):
        seen.append(request)
        if request.url.path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": identity, "verification_code": "AABBCC112233",
                "pairing_proof": proof, "expires_in": 300, "poll_interval": 3,
            })
        if request.url.path.endswith("/terminal-pairings/status/"):
            return httpx.Response(200, json={"state": "approved"})
        if request.url.path.endswith("/turns/"):
            payload = json.loads(request.content)
            assert payload == {"text": "Check Bell states"}
            assert request.headers["Idempotency-Key"]
            return httpx.Response(202, json={"run_id": run_id})
        return httpx.Response(401, json={"detail": "Revoked"})

    assert terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair",
         "send", str(conversation_id), "Check Bell states"],
        client_factory=lambda **kw: httpx.Client(
            transport=httpx.MockTransport(handler), **kw
        ),
    ) == 0
    assert seen[2].url.path.endswith(f"/conversations/{conversation_id}/turns/")
    assert run_id in capsys.readouterr().out


def test_browser_pair_denial_does_not_call_acp_gateway(capsys):
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": str(uuid4()), "verification_code": "AABBCC112233",
                "pairing_proof": "0123456789abcdefghijklmnopqrstuvwxyzPAIRING",
                "expires_in": 300, "poll_interval": 3,
            })
        return httpx.Response(410, json={"state": "expired_or_revoked"})

    status = terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair", "chats"],
        client_factory=lambda **kw: httpx.Client(
            transport=httpx.MockTransport(handler), **kw
        ),
    )
    assert status == 2
    assert len(calls) == 2
    assert "expired" in capsys.readouterr().err.lower()
