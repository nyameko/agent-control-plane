"""Ensure compatibility rollout accepts v3/v4 and rejects unknown versions.

The installed v4 migration must NOT be applied before compatible binaries are live.
"""
from unittest.mock import MagicMock

import pytest

from agent_control_plane import db


@pytest.mark.parametrize("version", [3, 4])
def test_ready_accepts_supported_versions(version):
    conn = MagicMock()
    conn.execute.return_value.fetchone.side_effect = [
        {"rolsuper": False, "rolbypassrls": False},
        {"version": version},
    ]
    db.ready(conn)


@pytest.mark.parametrize("version", [None, 2, 5])
def test_ready_rejects_unsupported_versions(version):
    conn = MagicMock()
    conn.execute.return_value.fetchone.side_effect = [
        {"rolsuper": False, "rolbypassrls": False},
        {"version": version} if version is not None else None,
    ]
    with pytest.raises(RuntimeError, match="migration"):
        db.ready(conn)


@pytest.mark.parametrize("field", ["rolsuper", "rolbypassrls"])
def test_ready_rejects_privileged_app_role(field):
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = {
        "rolsuper": field == "rolsuper",
        "rolbypassrls": field == "rolbypassrls",
    }
    with pytest.raises(RuntimeError, match="RLS"):
        db.ready(conn)
