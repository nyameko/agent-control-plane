"""The live acceptance script must be inert until explicitly opted in.

These smoke tests do not require PostgreSQL, credentials, a model, or network.
"""
import subprocess
import sys
from pathlib import Path

PROBE = Path(__file__).resolve().parents[1] / "scripts" / "m4b_live_acceptance.py"


def test_live_probe_is_inert_without_execute():
    result = subprocess.run(
        [sys.executable, str(PROBE), "--base-url", "https://example.invalid"],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert "no requests made" in result.stdout


def test_live_probe_rejects_remote_plain_http_before_checking_credentials():
    result = subprocess.run(
        [
            sys.executable, str(PROBE), "--base-url",
            "http://example.invalid", "--execute",
        ],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 2
    assert "Only HTTPS" in result.stderr
