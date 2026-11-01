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
