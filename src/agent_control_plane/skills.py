"""M4d: owner-scoped bindings to immutable, human-reviewed Git resources only.

The shipped catalog is empty by default. Entries can be added only in a
reviewed source PR, not via a model, assistant, browser POST or runtime API.
Binding a resource grants **no** model tools, filesystem or scheduler access.
"""
import json
import re
from importlib.resources import files
from uuid import uuid4

from agent_control_plane import db

_SHA = re.compile(r"^[a-f0-9]{40}$")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_NAME = re.compile(r"^[a-z][a-z0-9_.-]{0,119}$")
_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-.][a-z0-9]+)*$")


class SkillUnavailable(Exception):
    pass


class SkillNotReviewed(Exception):
    pass


class SkillConflict(Exception):
    pass


class SkillMissing(Exception):
    pass


def _trusted_catalog():
    manifest = json.loads(
        files("agent_control_plane").joinpath("reviewed_skills.json").read_text()
    )
    if manifest.get("catalog_version") != 1 or not isinstance(manifest.get("reviewed"), list):
        raise RuntimeError("Invalid operator skills catalog")
    items = {}
    for entry in manifest["reviewed"]:
        if not isinstance(entry, dict):
            raise RuntimeError("Invalid reviewed skill entry")
        expected = {
            "id", "version", "source_commit", "manifest_sha256", "reviewed_by",
            "resource_path", "required_capabilities", "automatic_code_execution",
        }
        if set(entry) != expected:
            raise RuntimeError("Reviewed skill catalog entry fields are invalid")
        if (
            not all(isinstance(entry[k], str) for k in
                    ("id", "version", "source_commit", "manifest_sha256",
                     "reviewed_by", "resource_path"))
            or not _NAME.fullmatch(entry["id"])
            or not _VERSION.fullmatch(entry["version"])
            or not _SHA.fullmatch(entry["source_commit"])
            or not _DIGEST.fullmatch(entry["manifest_sha256"])
            or not (1 <= len(entry["reviewed_by"]) <= 100)
            or entry["automatic_code_execution"] is not False
            or entry["required_capabilities"] != ["resource:read"]
        ):
            raise RuntimeError("Untrusted skill catalog entry")
        path = entry["resource_path"]
        if not (path.startswith("labs/") and path.endswith(".ipynb")
                and all(part not in {"", ".", ".."} for part in path.split("/"))
                and re.fullmatch(r"[A-Za-z0-9_./-]+", path)):
            raise RuntimeError("Untrusted resource path in skill catalog")
        key = (entry["id"], entry["version"])
        if key in items:
            raise RuntimeError("Duplicate reviewed skill")
        items[key] = entry
    return items


def _check_v8(conn):
    row = conn.execute(
        "SELECT max(version) AS version FROM acp1.schema_version"
    ).fetchone()
    if row is None or row["version"] < 8:
        raise SkillUnavailable


def catalog():
    return list(_trusted_catalog().values())


def _snapshot(conn, skill_id, version, *, lock=False):
    return conn.execute(
        "SELECT id,skill_id,version,source_commit,manifest_sha256,status,revision,"
        "created_at,updated_at,revoked_at FROM acp1.skill_binding "
        "WHERE skill_id=%s AND version=%s" + (" FOR UPDATE" if lock else ""),
        (skill_id, version),
    ).fetchone()


def bindings(conn, principal):
    trusted = _trusted_catalog()
    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v8(conn)
        rows = conn.execute(
            "SELECT id,skill_id,version,source_commit,manifest_sha256,status,"
            "revision,created_at,updated_at,revoked_at FROM acp1.skill_binding "
            "ORDER BY created_at DESC,id DESC LIMIT 100"
        ).fetchall()
    for row in rows:
        allowed = trusted.get((row["skill_id"], row["version"]))
        row["currently_reviewed"] = bool(
            allowed and allowed["source_commit"] == row["source_commit"].strip()
            and allowed["manifest_sha256"] == row["manifest_sha256"].strip()
        )
    return rows


def enable(conn, principal, skill_id, version, *, expected_revision):
    approved = _trusted_catalog().get((skill_id, version))
    if approved is None:
        raise SkillNotReviewed
    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v8(conn)
        current = _snapshot(conn, skill_id, version, lock=True)
        if current is None:
            if expected_revision != 0:
                raise SkillConflict
            binding_id = uuid4()
            conn.execute(
                "INSERT INTO acp1.skill_binding"
                "(id,tenant,owner_subject,skill_id,version,source_commit,"
                "manifest_sha256,status,revision) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,'enabled',1)",
                (binding_id, principal.tenant, principal.subject, skill_id,
                 version, approved["source_commit"], approved["manifest_sha256"]),
            )
            conn.execute(
                "INSERT INTO acp1.skill_binding_revision"
                "(binding_id,tenant,owner_subject,revision,action,actor_subject) "
                "VALUES (%s,%s,%s,1,'enabled',%s)",
                (binding_id, principal.tenant, principal.subject, principal.subject),
            )
            return _snapshot(conn, skill_id, version), True
        if current["revision"] != expected_revision:
            raise SkillConflict
        if (
            current["source_commit"].strip() != approved["source_commit"]
            or current["manifest_sha256"].strip() != approved["manifest_sha256"]
        ):
            raise SkillNotReviewed
        if current["status"] == "enabled":
            return current, False
        next_revision = current["revision"] + 1
        conn.execute(
            "INSERT INTO acp1.skill_binding_revision"
            "(binding_id,tenant,owner_subject,revision,action,actor_subject) "
            "VALUES (%s,%s,%s,%s,'enabled',%s)",
            (current["id"], principal.tenant, principal.subject, next_revision,
             principal.subject),
        )
        conn.execute(
            "UPDATE acp1.skill_binding SET status='enabled',revoked_at=NULL,revision=%s "
            "WHERE id=%s",
            (next_revision, current["id"]),
        )
        return _snapshot(conn, skill_id, version), True


def revoke(conn, principal, skill_id, version, *, expected_revision):
    with db.scoped(conn, principal.tenant, principal.subject):
        _check_v8(conn)
        current = _snapshot(conn, skill_id, version, lock=True)
        if current is None:
            raise SkillMissing
        if current["revision"] != expected_revision:
            raise SkillConflict
        if current["status"] == "revoked":
            return current, False
        next_revision = current["revision"] + 1
        conn.execute(
            "INSERT INTO acp1.skill_binding_revision"
            "(binding_id,tenant,owner_subject,revision,action,actor_subject) "
            "VALUES (%s,%s,%s,%s,'revoked',%s)",
            (current["id"], principal.tenant, principal.subject, next_revision,
             principal.subject),
        )
        conn.execute(
            "UPDATE acp1.skill_binding SET status='revoked',revoked_at=now(),revision=%s "
            "WHERE id=%s",
            (next_revision, current["id"]),
        )
        return _snapshot(conn, skill_id, version), True
