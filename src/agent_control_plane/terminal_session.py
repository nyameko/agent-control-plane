"""Small interactive ACP session designed to run inside an existing Herdr pane.

Only Quantum Platform verifies the human's signed identity. The short-lived
browser-approved proof stays in this process's memory; no config, history,
socket, shell environment or process command-line credential is created.
The portal rechecks approval/revocation on every request.
"""

from __future__ import annotations

import sys
from uuid import UUID, uuid4

import httpx

_GATEWAY = "/api/v1/agent/terminal-gateway"
_HELP = (
    "projects | chats | show <conversation-uuid> | send <conversation-uuid> <message>\n"
    "memories (approved, current) | new <title> | run <run-uuid> | connect | help | quit"
)


def _operation(line: str):
    """Parse only named ACP operations; never interpret the input as shell."""
    action, _, argument = line.partition(" ")
    argument = argument.strip()
    if action in ("projects", "chats", "memories") and not argument:
        path = {
            "projects": "/projects/", "chats": "/conversations/",
            "memories": "/memories/",
        }[action]
        return "GET", _GATEWAY + path, None, None
    if action in ("show", "run"):
        value = str(UUID(argument))
        if action == "show":
            return "GET", f"{_GATEWAY}/conversations/{value}/", None, None
        return "GET", f"{_GATEWAY}/runs/{value}/", None, None
    if action == "new" and 1 <= len(argument) <= 200:
        return "POST", _GATEWAY + "/conversations/", {"title": argument}, None
    if action == "send":
        conversation_id, sep, message = argument.partition(" ")
        message = message.strip()
        if sep and 1 <= len(message) <= 4000:
            value = str(UUID(conversation_id))
            return (
                "POST", f"{_GATEWAY}/conversations/{value}/turns/",
                {"text": message}, str(uuid4()),
            )
    raise ValueError("Invalid command or argument. Type 'help' for commands.")


def run_session(client: httpx.Client, endpoint: str, *, pairing, formatter) -> int:
    """One explicit approval per *short-lived* active terminal session.

    The backend expires pairings after five minutes, even if Herdr survives
    longer. No silent renewal and no cached, expired authorization.
    """
    headers = pairing(client, endpoint)
    print("ACP research session connected. Type 'help' or 'chats'.")
    print("Authorization is short-lived; type 'connect' when approval expires.")
    while True:
        try:
            sys.stdout.write("acp> ")
            sys.stdout.flush()
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            print("\nACP session closed.")
            return 0
        if not line:
            print()
            return 0
        line = line.strip()
        if not line:
            continue
        if line in ("quit", "exit"):
            return 0
        if line == "help":
            print(_HELP)
            continue
        if line == "connect":
            # Discard old proof BEFORE requesting fresh human approval.
            headers = {}
            try:
                headers = pairing(client, endpoint)
                print("Connected to Quantum Platform.")
            except (ValueError, httpx.RequestError) as exc:
                print(f"Approval unavailable: {exc}", file=sys.stderr)
            continue
        if not headers:
            print("Session not authorized. Type 'connect' and approve in browser.")
            continue
        try:
            method, path, body, key = _operation(line)
        except (ValueError, TypeError):
            print("Invalid command or argument. Type 'help' for commands.")
            continue

        request_headers = dict(headers)
        if key:
            request_headers["Idempotency-Key"] = key
        try:
            if method == "GET":
                reply = client.get(endpoint + path, headers=request_headers)
            else:
                reply = client.post(endpoint + path, headers=request_headers, json=body)
        except httpx.RequestError:
            # POST may have reached the server. Never silently resubmit it.
            print("Network request failed; verify server state before retrying.")
            continue
        if reply.status_code in (401, 403, 410):
            # Revoke RAM-only proof; never fall back to SSH/POSIX identity.
            headers = {}
            print("Terminal approval expired or revoked. Type 'connect' to reapprove.")
            continue
        if not reply.is_success:
            print(f"ACP request failed (HTTP {reply.status_code}).")
            continue
        try:
            print(formatter(reply.json()))
        except (ValueError, TypeError):
            print("ACP returned a response that could not be displayed.")
