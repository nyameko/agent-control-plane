"""M4g: a Herdr pane may reuse ONE portal approval for several ACP operations.

Mocks exercise the unchanged real Quantum Platform pairing/gateway paths.
No POSIX user/UID grants access; no token is written to files or stdout.
"""

from __future__ import annotations

import io
import json
import sys
from uuid import uuid4

import httpx

from agent_control_plane import terminal_client


def _client(handler):
    return lambda **kwargs: httpx.Client(transport=httpx.MockTransport(handler), **kwargs)


def test_interactive_pane_reuses_approval_and_conversation_uuid(capsys, monkeypatch):
    conversation = str(uuid4())
    pairing_id = str(uuid4())
    proof = "one-proof-only-in-memory-0123456789abcdefghijkl"
    calls = []

    def handler(request):
        calls.append(request)
        path = request.url.path
        if path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": pairing_id, "verification_code": "D00DFEED1234",
                "pairing_proof": proof, "expires_in": 300, "poll_interval": 3,
            })
        if path.endswith("/terminal-pairings/status/"):
            return httpx.Response(200, json={"state": "approved"})
        assert request.headers["X-ACP-Pairing-ID"] == pairing_id
        assert request.headers["Authorization"] == f"Pairing {proof}"
        if path.endswith("/terminal-gateway/conversations/"):
            return httpx.Response(200, json={"items": [{"id": conversation, "title": "C1"}]})
        if path.endswith(f"/conversations/{conversation}/"):
            return httpx.Response(200, json={"id": conversation, "messages": [
                {"author_kind": "human", "content": {"text": "M4g marker"}},
            ]})
        if path.endswith(f"/conversations/{conversation}/turns/"):
            assert request.headers.get("Idempotency-Key")
            assert json.loads(request.content) == {"text": "continue exact C1"}
            return httpx.Response(202, json={"run_id": str(uuid4())})
        raise AssertionError("unexpected route: " + path)

    monkeypatch.setattr(
        sys, "stdin", io.StringIO(
            f"chats\nshow {conversation}\nsend {conversation} continue exact C1\nquit\n"
        )
    )
    status = terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair", "session"],
        client_factory=_client(handler),
    )
    assert status == 0
    paths = [str(req.url.path) for req in calls]
    assert sum(path.endswith("/terminal-pairings/start/") for path in paths) == 1
    assert sum(path.endswith("/terminal-pairings/status/") for path in paths) == 1
    assert len(calls) == 5
    output = capsys.readouterr()
    assert conversation in output.out
    assert "M4g marker" in output.out
    assert "D00DFEED1234" in output.err
    assert proof not in output.out + output.err


def test_interactive_revocation_denies_next_request_without_hidden_reapproval(
    capsys, monkeypatch,
):
    pairing_id = str(uuid4())
    proof = "revoked-proof-only-in-memory-0123456789abcdefghijkl"
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": pairing_id, "verification_code": "D00DFEED1234",
                "pairing_proof": proof, "expires_in": 300, "poll_interval": 3,
            })
        if request.url.path.endswith("/terminal-pairings/status/"):
            return httpx.Response(200, json={"state": "approved"})
        return httpx.Response(401, json={"detail": "revoked"})

    monkeypatch.setattr(sys, "stdin", io.StringIO("chats\nchats\nquit\n"))
    assert terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair", "session"],
        client_factory=_client(handler),
    ) == 0
    assert len(calls) == 3
    out = capsys.readouterr()
    assert "expired or revoked" in out.out
    assert "not authorized" in out.out
    assert proof not in out.out + out.err


def test_interactive_session_refuses_bare_posix_or_raw_bearer(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("token\n"))
    assert terminal_client.main(
        ["--url", "https://quantum.example", "--token-stdin", "session"],
    ) == 2
    assert "--browser-pair" in capsys.readouterr().err


def test_interactive_invalid_command_never_reaches_gateway(capsys, monkeypatch):
    calls = []
    proof = "test-proof-only-in-memory-0123456789abcdefghijklm"

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": str(uuid4()), "verification_code": "D00DFEED1234",
                "pairing_proof": proof, "expires_in": 300, "poll_interval": 3,
            })
        if request.url.path.endswith("/terminal-pairings/status/"):
            return httpx.Response(200, json={"state": "approved"})
        raise AssertionError("Unexpected network command")

    monkeypatch.setattr(sys, "stdin", io.StringIO("rm -rf ~\nsend unknown prompt\nquit\n"))
    assert terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair", "session"],
        client_factory=_client(handler),
    ) == 0
    assert len(calls) == 2
    assert "Invalid command" in capsys.readouterr().out


def test_memory_readthrough_uses_portal_owner_and_never_caches(capsys, monkeypatch):
    from uuid import UUID
    memory_id = str(uuid4())
    pairing = str(uuid4())
    proof = "memory-readthrough-test-0123456789abcdefghijkl"
    requests = []
    revisions = iter((2, 3))

    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": pairing, "verification_code": "D00DFEED1234",
                "pairing_proof": proof, "expires_in": 300, "poll_interval": 3,
            })
        if request.url.path.endswith("/terminal-pairings/status/"):
            return httpx.Response(200, json={"state": "approved"})
        assert request.url.path == "/api/v1/agent/terminal-gateway/memories/"
        assert request.headers["Authorization"] == "Pairing " + proof
        assert UUID(request.headers["X-ACP-Pairing-ID"]) == UUID(pairing)
        revision = next(revisions)
        return httpx.Response(200, json={
            "items": [{
                "id": memory_id, "status": "active",
                "revision": revision,
                "body": f"Research note revision {revision}",
            }],
        })

    monkeypatch.setattr(sys, "stdin", io.StringIO("memories\nmemories\nquit\n"))
    assert terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair", "session"],
        client_factory=_client(handler),
    ) == 0
    out = capsys.readouterr()
    assert "[revision 2]" in out.out
    assert "[revision 3]" in out.out
    assert len(requests) == 4  # start, approve poll, two fresh memory reads
    assert proof not in out.out + out.err


def test_one_shot_memories_route_uses_portal_readonly(capsys):
    pairing = str(uuid4())
    proof = "memory-one-shot-test-0123456789abcdefghijkl"
    paths = []

    def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith("/terminal-pairings/start/"):
            return httpx.Response(201, json={
                "pairing_id": pairing, "verification_code": "D00DFEED1234",
                "pairing_proof": proof, "expires_in": 300, "poll_interval": 3,
            })
        if request.url.path.endswith("/terminal-pairings/status/"):
            return httpx.Response(200, json={"state": "approved"})
        assert request.url.path == "/api/v1/agent/terminal-gateway/memories/"
        return httpx.Response(200, json={"items": []})

    assert terminal_client.main(
        ["--url", "https://quantum.example", "--browser-pair", "memories"],
        client_factory=_client(handler),
    ) == 0
    assert paths[-1] == "/api/v1/agent/terminal-gateway/memories/"
    assert "No records" in capsys.readouterr().out
