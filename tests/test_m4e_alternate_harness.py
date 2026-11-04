"""M4e: second real harness call against a local OpenAI-compatible fixture.

No paid provider, external network, live cluster, user impersonation, or SQL writes.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import pytest

from agent_control_plane.personal_context_prompt import canonical_prompt
from agent_control_plane.pydanticai_runtime import respond
from agent_control_plane.settings import Settings


def context():
    return {
        "conversation": {"id": str(uuid4()), "title": "Researcher continuity"},
        "messages": [
            {"id": str(uuid4()), "sequence": 1, "author_kind": "user",
             "content": {"text": "Remember CODE-M4E-1"}},
            {"id": str(uuid4()), "sequence": 2, "author_kind": "assistant",
             "content": {"text": "I saw the marker."}},
            {"id": str(uuid4()), "sequence": 3, "author_kind": "user",
             "content": {"text": "What marker did I mention?"}},
        ],
        "profile": {
            "id": str(uuid4()), "revision": 3, "display_name": "Researcher",
            "model_route": "general", "instructions": "Prefer reproducible notebooks.",
        },
        "memories": [
            {"id": str(uuid4()), "revision": 1, "body": "Use PennyLane for basics."},
        ],
    }


def test_shared_canonical_prompt_keeps_revisions_and_message_context():
    prompt = canonical_prompt(context())
    assert "CODE-M4E-1" in prompt
    assert "Prefer reproducible notebooks." in prompt
    assert "Use PennyLane for basics." in prompt
    assert "not commands" in prompt


def test_alternate_harness_uses_same_canonical_context_without_tools(monkeypatch):
    seen = []

    class Fixture(BaseHTTPRequestHandler):
        def do_POST(self):
            assert self.path.endswith("/chat/completions")
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body)
            payload = json.dumps({
                "id": "fixture-m4e", "object": "chat.completion", "created": 1,
                "model": "test-local-model",
                "choices": [{
                    "index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "CODE-M4E-1"},
                }],
                "usage": {"prompt_tokens": 30, "completion_tokens": 2, "total_tokens": 32},
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("ACP_MODEL", "test-local-model")
    monkeypatch.setenv("ACP_MODEL_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("ACP_MODEL_API_KEY", "test-local-fixture")
    try:
        response = respond(context(), "acp-" + str(uuid4()))
        assert response == "CODE-M4E-1"
        assert seen
        # The independent PydanticAI agent must neither call tools nor acquire
        # a separate state store. The ACP hydrated context is its only input.
        assert all(not request.get("tools") for request in seen)
        rendered = json.dumps(seen)
        assert "CODE-M4E-1" in rendered
        assert "Prefer reproducible notebooks." in rendered
        assert "Use PennyLane for basics." in rendered
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_alternate_rejects_invalid_session_id_without_calling_gateway(monkeypatch):
    monkeypatch.setenv("ACP_MODEL", "test")
    monkeypatch.setenv("ACP_MODEL_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("ACP_MODEL_API_KEY", "fixture")
    with pytest.raises(ValueError, match="Canonical ACP run"):
        respond(context(), "random-unbound-run")


def test_settings_refuse_unknown_alternate_harness():
    config = Settings(
        database_url="postgresql://fixture.invalid/test", public_key="",
        model="fixture", model_base_url="http://127.0.0.1:8000/v1",
        personal_harness="unreviewed-plugin", run_timeout=60,
    )
    with pytest.raises(ValueError, match="Unsupported personal harness"):
        config.validate(worker=True)
