"""M4a personal worker: hydrate canonical ACP context, run Hermes, commit response."""

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
from agent_control_plane.hermes_runtime import HERMES_REVISION
from agent_control_plane.settings import Settings

logger = logging.getLogger(__name__)
PROFILE_CONFIG = """plugins:
  enabled: []
  disabled: []
memory:
  memory_enabled: false
  user_profile_enabled: false
"""


class PersonalRuntimeFailure(Exception):
    pass


def heartbeat(conn):
    conn.execute("SELECT 1")
    Path("/tmp/acp-personal-worker-heartbeat").touch()


def run_hermes(conn, settings, run, context):
    with tempfile.TemporaryDirectory(prefix="acp-personal-run-") as directory:
        root = Path(directory)
        profile = root / "profile"
        profile.mkdir()
        (profile / "config.yaml").write_text(PROFILE_CONFIG)
        request_path = root / "input.json"
        result_path = root / "result.json"
        request_path.write_text(
            json.dumps(
                {"context": context, "session_id": f"acp-{run['id']}"},
                default=str,
            )
        )
        environment = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONUNBUFFERED": "1",
            "HERMES_HOME": str(profile),
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
                "agent_control_plane.personal_runtime",
                str(request_path),
                str(result_path),
            ],
            env=environment,
            cwd=profile,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + settings.run_timeout
        try:
            while process.poll() is None:
                heartbeat(conn)
                if time.monotonic() >= deadline:
                    raise PersonalRuntimeFailure("personal_runtime_timeout")
                time.sleep(1)
            if process.returncode != 0 or not result_path.exists():
                raise PersonalRuntimeFailure("personal_runtime_failed")
            if result_path.stat().st_size > 100000:
                raise PersonalRuntimeFailure("personal_runtime_invalid_response")
            response = json.loads(result_path.read_text())["response"]
            if not isinstance(response, str) or not response.strip() or len(response) > 30000:
                raise PersonalRuntimeFailure("personal_runtime_invalid_response")
            return response
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def run_once(conn, settings, *, responder=run_hermes):
    run = db.claim_personal(conn, settings, HERMES_REVISION)
    if not run:
        return False
    try:
        context = db.hydrate_personal_context(conn, settings.tenant, run)
        response = responder(conn, settings, run, context)
        db.finish_personal(conn, settings.tenant, run, response)
    except PersonalRuntimeFailure as exc:
        db.finish_personal(conn, settings.tenant, run, None, failure=str(exc))
    except Exception as exc:
        logger.error("Personal run %s failed (%s)", run["id"], type(exc).__name__)
        db.finish_personal(conn, settings.tenant, run, None, failure="worker_error")
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
    with db.connection(settings.database_url) as conn:
        db.ready(conn)
        acquired = conn.execute(
            "SELECT pg_try_advisory_lock(%s,%s) AS acquired", db.PERSONAL_WORKER_LOCK
        ).fetchone()["acquired"]
        if not acquired:
            raise RuntimeError("Another personal worker holds the database lock")
        db.recover_interrupted_personal(conn, settings.tenant)
        while True:
            heartbeat(conn)
            if not run_once(conn, settings):
                time.sleep(2)


if __name__ == "__main__":
    main()
