"""Singleton worker; PostgreSQL queue, bounded Hermes process, durable evidence."""

import fcntl
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from agent_control_plane import db
from agent_control_plane.diagnostic import DiagnosticFailure, pod_readiness
from agent_control_plane.hermes_runtime import HERMES_REVISION, SOUL
from agent_control_plane.settings import Settings

logger = logging.getLogger(__name__)
PROFILE_CONFIG = """plugins:
  enabled: []
  disabled: []
memory:
  memory_enabled: false
  user_profile_enabled: false
"""


def heartbeat(conn):
    conn.execute("SELECT 1")
    Path("/tmp/acp-worker-heartbeat").touch()


def summarize(conn, settings, run, evidence):
    with tempfile.TemporaryDirectory(prefix="acp-run-") as directory:
        request_path, result_path = Path(directory) / "input.json", Path(directory) / "result.json"
        request_path.write_text(
            json.dumps(
                {
                    "evidence": evidence,
                    "session_id": f"acp-{run['id']}",
                }
            )
        )
        environment = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONUNBUFFERED": "1",
            "HERMES_HOME": settings.profile_home,
            "HERMES_ENABLE_PROJECT_PLUGINS": "0",
            "ACP_MODEL": settings.model,
            "ACP_MODEL_BASE_URL": settings.model_base_url,
            "ACP_MODEL_API_KEY": os.environ["ACP_MODEL_API_KEY"],
            "ACP_RUN_TIMEOUT_SECONDS": str(settings.run_timeout),
        }
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "agent_control_plane.hermes_runtime",
                str(request_path),
                str(result_path),
            ],
            env=environment,
            cwd=settings.profile_home,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + settings.run_timeout
        try:
            while process.poll() is None:
                heartbeat(conn)
                if time.monotonic() >= deadline:
                    raise DiagnosticFailure("hermes_timeout")
                time.sleep(1)
            if process.returncode != 0 or not result_path.exists():
                raise DiagnosticFailure("hermes_failed")
            if result_path.stat().st_size > 100000:
                raise DiagnosticFailure("hermes_invalid_response")
            summary = json.loads(result_path.read_text())["summary"]
            if not isinstance(summary, str) or not summary.strip() or len(summary) > 20000:
                raise DiagnosticFailure("hermes_invalid_response")
            return summary
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def run_once(conn, settings, *, diagnostic=pod_readiness, explainer=summarize):
    run = db.claim(conn, settings, HERMES_REVISION)
    if not run:
        return False
    try:
        evidence = diagnostic(settings.prometheus_url)
        db.save_evidence(conn, settings.tenant, run["id"], evidence)
        summary = explainer(conn, settings, run, evidence)
        db.finish(conn, settings.tenant, run["id"], summary=summary)
    except DiagnosticFailure as exc:
        db.finish(conn, settings.tenant, run["id"], failure=exc.code)
    except Exception as exc:
        logger.error("Run %s failed (%s)", run["id"], type(exc).__name__)
        db.finish(conn, settings.tenant, run["id"], failure="worker_error")
    return True


def main():
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    settings.validate(worker=True)
    if not os.environ.get("ACP_MODEL_API_KEY"):
        raise RuntimeError(
            "ACP_MODEL_API_KEY is required (use an explicit local key if unauthenticated)"
        )
    os.umask(0o077)
    home = Path(settings.profile_home)
    home.mkdir(parents=True, exist_ok=True)
    with (home / ".worker.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (home / "config.yaml").write_text(PROFILE_CONFIG)
        (home / "SOUL.md").write_text(SOUL)
        with db.connection(settings.database_url) as conn:
            db.ready(conn)
            acquired = conn.execute(
                "SELECT pg_try_advisory_lock(%s,%s) AS acquired", db.WORKER_LOCK
            ).fetchone()["acquired"]
            if not acquired:
                raise RuntimeError("Another administrative worker holds the database lock")
            db.recover_interrupted(conn, settings.tenant)
            while True:
                heartbeat(conn)
                if not run_once(conn, settings):
                    time.sleep(2)


if __name__ == "__main__":
    main()
