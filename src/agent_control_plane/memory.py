"""Explicit, private ACP memory lifecycle backed by the schema-v4 revision ledger.

No automatic extraction, model-based promotion or Hermes-native storage.
All reads and writes run within the signed principal's PostgreSQL RLS scope.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from agent_control_plane import db


class MemoryConflict(Exception):
    """Stale revision, conflicting idempotency key or invalid transition."""


class MemoryMissing(Exception):
    """Absent or unauthorized source/memory. Do not reveal which one."""


class MemoryUnavailable(Exception):
    """The explicitly enabled memory API requires schema version 4."""


class MemoryInvalid(Exception):
    """Invalid or potentially sensitive content."""


# Defense in depth only. This cannot detect every credential or sensitive fact.
_SECRET = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})",
    flags=re.IGNORECASE,
)


def _digest(value):
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _check_v4(conn):
    version = conn.execute(
        "SELECT version FROM acp1.schema_version ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if version is None or version["version"] != 4:
        raise MemoryUnavailable


def _safe_text(body):
    if _SECRET.search(body):
        raise MemoryInvalid("Memory text appears to contain a credential")
    return body


_SNAPSHOT = (
    "SELECT i.id,i.status,i.kind,i.scope_kind,i.current_revision AS revision,"
    "i.source_conversation_id,i.source_message_id,i.source_sha256,"
    "i.sensitivity,i.verification_status,i.expires_at,i.approved_at,"
    "i.revoked_at,i.created_at,i.updated_at,"
    "r.body,r.event_type,r.actor_subject,r.reason "
    "FROM acp1.memory_item i JOIN acp1.memory_revision r "
    "ON r.tenant=i.tenant AND r.owner_subject=i.owner_subject "
    "AND r.memory_id=i.id AND r.revision=i.current_revision "
)


def _record(conn, memory_id, *, lock=False):
    suffix = " FOR UPDATE OF i" if lock else ""
    return conn.execute(_SNAPSHOT + "WHERE i.id=%s" + suffix, (memory_id,)).fetchone()


def create_candidate(conn, principal, key, request):
    data = request.model_dump(mode="json")
    payload_digest = _digest(data)
    _safe_text(request.body)
    if request.expires_at is not None and request.expires_at <= datetime.now(timezone.utc):
        raise MemoryInvalid("Expiration must be in the future")

    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v4(conn)
        existing = conn.execute(
            "SELECT id,creation_payload_sha256 FROM acp1.memory_item "
            "WHERE creation_key=%s FOR UPDATE",
            (key,),
        ).fetchone()
        if existing:
            if existing["creation_payload_sha256"].strip() != payload_digest:
                raise MemoryConflict
            return _record(conn, existing["id"]), False

        source = conn.execute(
            "SELECT m.content FROM acp1.message m "
            "JOIN acp1.conversation c ON c.tenant=m.tenant "
            "AND c.owner_subject=m.owner_subject AND c.id=m.conversation_id "
            "WHERE m.id=%s AND m.conversation_id=%s "
            "AND m.author_kind='user' AND c.archived_at IS NULL",
            (request.source_message_id, request.source_conversation_id),
        ).fetchone()
        if source is None:
            raise MemoryMissing
        memory_id = uuid4()
        inserted = conn.execute(
            "INSERT INTO acp1.memory_item "
            "(id,tenant,owner_subject,creation_key,creation_payload_sha256,"
            "kind,source_conversation_id,source_message_id,source_sha256,"
            "sensitivity,expires_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT (tenant,owner_subject,creation_key) DO NOTHING RETURNING id",
            (
                memory_id, principal.tenant, principal.subject, key, payload_digest,
                request.kind, request.source_conversation_id,
                request.source_message_id, _digest(source["content"]),
                request.sensitivity, request.expires_at,
            ),
        ).fetchone()
        if inserted is None:
            # Concurrent replay: respect the unique idempotency key and payload digest.
            existing = conn.execute(
                "SELECT id,creation_payload_sha256 FROM acp1.memory_item "
                "WHERE creation_key=%s",
                (key,),
            ).fetchone()
            if existing is None or existing["creation_payload_sha256"].strip() != payload_digest:
                raise MemoryConflict
            return _record(conn, existing["id"]), False
        conn.execute(
            "INSERT INTO acp1.memory_revision "
            "(memory_id,tenant,owner_subject,revision,event_type,body,actor_subject) "
            "VALUES (%s,%s,%s,1,'candidate_created',%s,%s)",
            (memory_id, principal.tenant, principal.subject, request.body, principal.subject),
        )
        return _record(conn, memory_id), True


def transition(conn, principal, memory_id, expected_revision, action, *, body=None, reason=None):
    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v4(conn)
        current = _record(conn, memory_id, lock=True)
        if current is None:
            raise MemoryMissing
        if current["revision"] != expected_revision:
            raise MemoryConflict
        status = current["status"]
        if action == "approved" and status == "candidate":
            if current["expires_at"] and current["expires_at"] <= datetime.now(timezone.utc):
                raise MemoryConflict
            text = _safe_text(body if body is not None else current["body"])
            assignment = "status='active',approved_at=now()"
        elif action == "corrected" and status == "active":
            text = _safe_text(body)
            assignment = "status='active'"
        elif action == "revoked" and status in {"candidate", "active"}:
            text = None
            assignment = "status='revoked',revoked_at=now()"
        else:
            raise MemoryConflict
        revision = current["revision"] + 1
        conn.execute(
            "INSERT INTO acp1.memory_revision "
            "(memory_id,tenant,owner_subject,revision,event_type,body,actor_subject,reason) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                memory_id, principal.tenant, principal.subject, revision,
                action, text, principal.subject, reason,
            ),
        )
        conn.execute(
            f"UPDATE acp1.memory_item SET {assignment},current_revision=%s WHERE id=%s",
            (revision, memory_id),
        )
        return _record(conn, memory_id)


def get_memory(conn, principal, memory_id):
    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v4(conn)
        record = _record(conn, memory_id)
        if record is None:
            raise MemoryMissing
        return record


def list_memories(conn, principal, status=None):
    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v4(conn)
        where = "WHERE i.status=%s " if status is not None else ""
        args = (status,) if status is not None else ()
        return conn.execute(
            _SNAPSHOT + where + "ORDER BY i.updated_at DESC,i.id DESC LIMIT 100",
            args,
        ).fetchall()


def retrieve(conn, principal, limit=8):
    """Deterministic authorized retrieval, bounded to 6,000 total body characters."""
    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v4(conn)
        rows = conn.execute(
            _SNAPSHOT
            + "WHERE i.scope_kind='private_user' AND i.status='active' "
            "AND i.approved_at IS NOT NULL "
            "AND (i.expires_at IS NULL OR i.expires_at > now()) "
            "AND r.body IS NOT NULL "
            "ORDER BY i.updated_at DESC,i.id DESC LIMIT 100"
        ).fetchall()
        selected, total = [], 0
        for row in rows:
            length = len(row["body"])
            if total + length > 6000:
                continue
            selected.append(row)
            total += length
            if len(selected) >= limit:
                break
        return selected
