"""Thin SSH/terminal client for canonical ACP records; no auth broker or shell hooks.

A trusted Quantum Platform session broker must issue short-lived, subject-scoped
assertions. This client never accepts UID, tenant, signing keys or passwords as
identity proof; it only forwards an already issued one-use/short-lived bearer
read from stdin. Do not persist tokens in shell history or configuration.
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx


def validated_url(url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.username or parsed.password or parsed.query or parsed.fragment
        or not parsed.hostname or parsed.path not in ("", "/")
        or parsed.scheme not in {"http", "https"}
        or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"})
    ):
        raise ValueError("Use an HTTPS ACP endpoint (or local loopback for tests)")
    return url.rstrip("/")


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        prog="acp", description="Terminal access to canonical research conversations"
    )
    cli.add_argument("--url", required=True, help="Trusted HTTPS ACP API endpoint")
    cli.add_argument(
        "--token-stdin", action="store_true", required=True,
        help="Read one short-lived broker-issued assertion from stdin",
    )
    sub = cli.add_subparsers(dest="command", required=True)
    sub.add_parser("projects", help="List private projects")
    sub.add_parser("chats", help="List private conversations")
    show = sub.add_parser("show", help="Display one conversation")
    show.add_argument("conversation_id", type=UUID)
    send = sub.add_parser("send", help="Submit a turn to an existing conversation")
    send.add_argument("conversation_id", type=UUID)
    send.add_argument("text", nargs="?", help="Message text (omit to read from stdin)")
    run = sub.add_parser("run", help="Show the status of a submitted run")
    run.add_argument("run_id", type=UUID)
    cli.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable view")
    return cli


def _format(result, *, json_mode=False):
    if json_mode:
        return json.dumps(result, indent=2, default=str)
    if isinstance(result, dict) and "items" in result:
        return "\n".join(
            f"{row.get('id', '')}\t{row.get('title', row.get('status', ''))}"
            for row in result["items"]
        ) or "No records."
    if isinstance(result, dict) and "messages" in result:
        messages = result["messages"]
        lines = []
        for row in messages:
            content = row.get("content")
            text = (
                content.get("text", "[structured message]")
                if isinstance(content, dict) else str(content)
            )
            lines.append(f"{row.get('author_kind', 'unknown')}: {text}")
        return "\n".join(lines) or "No messages."
    return json.dumps(result, indent=2, default=str)


def main(argv=None, *, client_factory=httpx.Client) -> int:
    args = parser().parse_args(argv)
    try:
        endpoint = validated_url(args.url)
        # Token comes from the trusted local broker's pipe, never --token on argv.
        token = sys.stdin.readline().strip()
        if not token or len(token) > 8192 or "\n" in token:
            raise ValueError("No valid short-lived assertion provided by stdin")
        url = {
            "projects": "/v1/projects",
            "chats": "/v1/conversations",
            "show": f"/v1/conversations/{args.conversation_id}" if args.command == "show" else "",
            "send": (
                f"/v1/conversations/{args.conversation_id}/turns"
                if args.command == "send" else ""
            ),
            "run": f"/v1/runs/{args.run_id}" if args.command == "run" else "",
        }[args.command]
        # Without a trusted identity exchange, no production login-node activation.
        headers = {"Authorization": "Bearer " + token}
        payload = None
        if args.command == "send":
            if args.text:
                message = args.text
            else:
                # An already consumed token line leaves the rest of the pipe as the turn.
                message = sys.stdin.read().strip()
            if not message or len(message) > 4000:
                raise ValueError("Turn text must be 1–4000 characters")
            payload = {
                "content": {"text": message},
                "source_channel": "ssh",
                "client_message_id": str(uuid4()),
            }
            headers["Idempotency-Key"] = str(uuid4())
        with client_factory(timeout=15, follow_redirects=False) as client:
            reply = client.post(endpoint + url, headers=headers, json=payload) if payload else (
                client.get(endpoint + url, headers=headers)
            )
        if reply.status_code in {401, 403}:
            print(
                "Session not authorized or expired. Reauthenticate using the trusted broker.",
                file=sys.stderr,
            )
            return 3
        if not reply.is_success:
            print(f"ACP request failed (HTTP {reply.status_code}).", file=sys.stderr)
            return 2
        print(_format(reply.json(), json_mode=args.json))
        return 0
    except (ValueError, httpx.RequestError, json.JSONDecodeError) as exc:
        print(f"ACP client: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
