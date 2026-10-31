#!/usr/bin/env python3
"""Opt-in live M4b API acceptance probe. Never manages Kubernetes or migrations.

Usage (tokens stay in the process environment, not command-line arguments):
  ACP_M4B_TEST_TOKEN=... ACP_M4B_OTHER_TOKEN=... \
    python scripts/m4b_live_acceptance.py --base-url https://... --execute

This creates synthetic personal conversations and a temporary approved memory.
The memory is revoked in a finally block, including on assertion failure.
"""
import argparse
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx


def require(response, statuses=(200,)):
    if response.status_code not in statuses:
        # Do not print response bodies; they may contain private conversations.
        raise RuntimeError(
            f"{response.request.method} {response.request.url.path}: "
            f"HTTP {response.status_code}, expected {statuses}"
        )
    return response.json()


def conversation(client, title):
    return require(client.post("/v1/conversations", json={"title": title}), (201,))["id"]


def turn(client, conversation_id, question, *, timeout_seconds):
    queued = require(
        client.post(
            f"/v1/conversations/{conversation_id}/turns",
            headers={"Idempotency-Key": str(uuid4())},
            json={"content": question, "source_channel": "api"},
        ),
        (202, 200),
    )
    run_id = queued["run_id"]
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        run = require(client.get(f"/v1/runs/{run_id}"))
        if run["status"] == "succeeded":
            history = require(client.get(f"/v1/conversations/{conversation_id}"))
            for message in reversed(history["messages"]):
                if message["author_kind"] == "assistant":
                    content = message["content"]
                    return content.get("text", "") if isinstance(content, dict) else str(content)
            raise RuntimeError("Successful run has no visible canonical assistant message")
        if run["status"] == "failed":
            raise RuntimeError(f"Agent run failed ({run.get('failure_code', 'unknown')})")
        time.sleep(2)
    raise RuntimeError("Timed out waiting for a canonical agent run")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", required=True, help="Explicit ACP API origin, not the portal UI"
    )
    parser.add_argument("--execute", action="store_true", help="Required to create test data")
    parser.add_argument("--pause-for-restart", action="store_true",
                        help="Manually approved API/worker restart before fresh C2")
    parser.add_argument("--timeout-seconds", type=int, default=240)
    args = parser.parse_args()

    url = httpx.URL(args.base_url)
    if url.scheme != "https" and not (
        url.scheme == "http" and url.host in {"localhost", "127.0.0.1", "::1"}
    ):
        parser.error("Only HTTPS, or HTTP to loopback, is allowed for bearer tokens")
    if not args.execute:
        print("DRY RUN: no requests made. Add --execute to create synthetic test data.")
        return 0

    token = os.environ.get("ACP_M4B_TEST_TOKEN", "")
    other_token = os.environ.get("ACP_M4B_OTHER_TOKEN", "")
    if not token:
        parser.error("Set ACP_M4B_TEST_TOKEN (a short-lived signed agent:personal assertion)")
    if not 15 <= args.timeout_seconds <= 900:
        parser.error("--timeout-seconds must be between 15 and 900")

    marker = uuid4().hex[:12]
    first_body = f"For quantum-computing introductory demos, I prefer PennyLane (test {marker})."
    second_body = f"For quantum-computing introductory demos, I prefer Qiskit (test {marker})."
    memory_id = None
    revision = None
    revoked = False
    checks = []
    headers = {"Authorization": f"Bearer {token}"}

    with httpx.Client(base_url=args.base_url.rstrip("/"), headers=headers, timeout=20) as client:
        try:
            c1 = conversation(client, "M4b synthetic C1 source")
            source = require(
                client.post(
                    f"/v1/conversations/{c1}/messages",
                    json={
                        "author_kind": "user",
                        "content": {"text": first_body},
                        "source_channel": "api",
                    },
                ),
                (201,),
            )
            candidate = require(
                client.post(
                    "/v1/memories/candidates",
                    headers={"Idempotency-Key": str(uuid4())},
                    json={
                        "source_conversation_id": c1,
                        "source_message_id": source["id"],
                        "kind": "preference",
                        "body": first_body,
                    },
                ),
                (201,),
            )
            memory_id, revision = candidate["id"], candidate["revision"]
            assert candidate["status"] == "candidate"
            assert all(
                item["id"] != memory_id
                for item in require(client.get("/v1/memories/retrieve"))["items"]
            ), "Candidate leaked into retrieval"
            checks.append("candidate_not_retrieved")

            approval = require(
                client.post(
                    f"/v1/memories/{memory_id}/approve",
                    headers={"If-Match": f'"{revision}"'},
                    json={},
                )
            )
            revision = approval["revision"]
            assert approval["status"] == "active"
            assert any(
                item["id"] == memory_id and item["body"] == first_body
                for item in require(client.get("/v1/memories/retrieve"))["items"]
            ), "Approved memory not retrievable"
            checks.append("approval_and_source_lookup")

            if args.pause_for_restart:
                print("PAUSED: obtain separate operator approval and replace API/worker "
                      "Pods and ephemeral Hermes state; verify readiness.")
                input("Press Enter only AFTER observing the approved restart: ")

            c2 = conversation(client, "M4b synthetic C2 recall")
            response = turn(
                client, c2, "Which SDK do I explicitly prefer for introductory quantum demos?",
                timeout_seconds=args.timeout_seconds,
            )
            assert "pennylane" in response.casefold(), "Fresh C2 did not recall PennyLane"
            checks.append("fresh_c2_model_recall")

            correction = require(
                client.patch(
                    f"/v1/memories/{memory_id}",
                    headers={"If-Match": f'"{revision}"'},
                    json={"body": second_body, "reason": "Synthetic conformance correction"},
                )
            )
            revision = correction["revision"]
            assert correction["status"] == "active"
            retrieved = require(client.get("/v1/memories/retrieve"))["items"]
            assert any(
                i["id"] == memory_id and i["body"] == second_body for i in retrieved
            ), "Correction not visible in retrieval"
            checks.append("correction_revision")

            c3 = conversation(client, "M4b synthetic C3 corrected recall")
            response = turn(
                client, c3, "Which SDK do I explicitly prefer for introductory quantum demos?",
                timeout_seconds=args.timeout_seconds,
            )
            assert "qiskit" in response.casefold(), "Fresh C3 did not recall corrected Qiskit"
            checks.append("fresh_c3_corrected_model_recall")

            if other_token:
                with httpx.Client(
                    base_url=args.base_url.rstrip("/"),
                    headers={"Authorization": f"Bearer {other_token}"},
                    timeout=20,
                ) as other:
                    denied = other.get(f"/v1/memories/{memory_id}")
                    assert denied.status_code == 404, "Other user can read memory"
                    foreign = require(other.get("/v1/memories/retrieve"))["items"]
                    assert all(i["id"] != memory_id for i in foreign), "Cross-user retrieval"
                    denied = other.post(
                        f"/v1/memories/{memory_id}/revoke",
                        headers={"If-Match": f'"{revision}"'}, json={},
                    )
                    assert denied.status_code == 404, "Other user can revoke memory"
                checks.append("second_user_denied")
            else:
                print("INCOMPLETE: ACP_M4B_OTHER_TOKEN absent; second-user gate not tested.")

            expired = client.post(
                "/v1/memories/candidates",
                headers={"Idempotency-Key": str(uuid4())},
                json={
                    "source_conversation_id": c1,
                    "source_message_id": source["id"],
                    "kind": "preference", "body": first_body,
                    "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
                },
            )
            assert expired.status_code == 422, "Past expiry not rejected"
            checks.append("past_expiry_rejected")

            result = require(
                client.post(
                    f"/v1/memories/{memory_id}/revoke",
                    headers={"If-Match": f'"{revision}"'}, json={"reason": "Test cleanup"},
                )
            )
            revision, revoked = result["revision"], True
            assert result["status"] == "revoked"
            assert all(
                i["id"] != memory_id
                for i in require(client.get("/v1/memories/retrieve"))["items"]
            ), "Revoked memory leaked into retrieval"
            checks.append("revoked_not_retrieved")

            # A generative response cannot prove absence; API/RLS and worker
            # hydration conformance must establish no revoked material is sent.
            c4 = conversation(client, "M4b synthetic C4 after revocation")
            turn(
                client, c4, "Do I have a saved preference for a quantum demos SDK?",
                timeout_seconds=args.timeout_seconds,
            )
            checks.append("fresh_c4_model_turn_after_revocation")
            print("PASS (API/model observations): " + ", ".join(checks))
            print("NOT YET PROVEN BY THIS RUNNER: actual Pod restarts unless paused "
                  "and externally witnessed; source deletion; SQL RLS; browser/Jupyter "
                  "continuity; absence from model inputs; disaster recovery.")
            print("Synthetic memory ID prefix: " + memory_id[:8])
            return 0
        finally:
            if memory_id and not revoked and revision is not None:
                try:
                    require(
                        client.post(
                            f"/v1/memories/{memory_id}/revoke",
                            headers={"If-Match": f'"{revision}"'},
                            json={"reason": "Aborted acceptance probe cleanup"},
                        )
                    )
                    print("Cleanup: synthetic memory revoked.")
                except Exception:
                    print("WARNING: cleanup failed; manually revoke synthetic "
                          f"memory ID prefix {memory_id[:8]} in the researcher UI.",
                          file=sys.stderr)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, AssertionError, httpx.HTTPError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
