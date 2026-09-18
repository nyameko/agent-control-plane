"""Actual pinned Hermes SDK, with a local OpenAI protocol fixture (no real inference)."""

import json
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import pytest

from agent_control_plane.hermes_runtime import SOUL
from agent_control_plane.settings import Settings
from agent_control_plane.worker import PROFILE_CONFIG, summarize


@pytest.mark.skipif(
    not os.getenv("ACP_TEST_HERMES"), reason="Set ACP_TEST_HERMES=1 with pinned SDK"
)
def test_pinned_sdk_empty_tools_and_persistent_session(tmp_path, monkeypatch):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(body)
            payload = json.dumps(
                {
                    "id": "fixture-completion",
                    "object": "chat.completion",
                    "created": 1,
                    "model": "test-model",
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {
                                "role": "assistant",
                                "content": "Two pods have Ready=true.",
                            },
                        }
                    ],
                    "usage": {"prompt_tokens": 30, "completion_tokens": 10, "total_tokens": 40},
                }
            ).encode()
            if body.get("stream"):
                chunks = [
                    {
                        "id": "fixture",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": "test-model",
                        "choices": [
                            {
                                "index": 0,
                                "finish_reason": None,
                                "delta": {
                                    "role": "assistant",
                                    "content": "Two pods have Ready=true.",
                                },
                            }
                        ],
                    },
                    {
                        "id": "fixture",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": "test-model",
                        "choices": [{"index": 0, "finish_reason": "stop", "delta": {}}],
                    },
                ]
                payload = (
                    "".join("data: " + json.dumps(c) + "\n\n" for c in chunks) + "data: [DONE]\n\n"
                ).encode()
            self.send_response(200)
            self.send_header(
                "Content-Type", "text/event-stream" if body.get("stream") else "application/json"
            )
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_ENABLE_PROJECT_PLUGINS", "0")
    monkeypatch.setenv("ACP_MODEL", "test-model")
    monkeypatch.setenv("ACP_MODEL_API_KEY", "local-fixture-only")
    monkeypatch.setenv("ACP_MODEL_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("ACP_RUN_TIMEOUT_SECONDS", "30")
    (tmp_path / "config.yaml").write_text(PROFILE_CONFIG)
    (tmp_path / "SOUL.md").write_text(SOUL)
    run_id = uuid4()
    session_id = "acp-" + str(run_id)

    class HeartbeatConnection:
        def execute(self, query):
            assert query == "SELECT 1"

    config = Settings(
        database_url="",
        public_key="",
        model="test-model",
        model_base_url=os.environ["ACP_MODEL_BASE_URL"],
        profile_home=str(tmp_path),
        run_timeout=30,
    )
    try:
        result = summarize(
            HeartbeatConnection(),
            config,
            {"id": run_id},
            {"counts": {"true": 2}, "observed_at": "2026-09-17T00:00:00Z"},
        )
        assert result == "Two pods have Ready=true."
        assert calls and all(not call.get("tools") for call in calls)
        # Reopen the runtime's real SQLite database after the adapter closed it.
        with sqlite3.connect(tmp_path / "state.db") as conn:
            assert conn.execute("SELECT id FROM sessions WHERE id=?", (session_id,)).fetchone()
            assert (
                conn.execute(
                    "SELECT count(*) FROM messages WHERE session_id=?", (session_id,)
                ).fetchone()[0]
                >= 2
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
