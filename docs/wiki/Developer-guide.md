# Developer guide

## Working environment

ACP is Python/FastAPI/PostgreSQL, with `requires-python >=3.13,<3.15`. Run local tests in a disposable environment; never reuse the production database.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check src tests scripts
pytest
```

Tests requiring PostgreSQL need a dedicated disposable DSN and schema owner/app roles configured according to test documentation. `python -m agent_control_plane` starts a loopback development API on port 8080 but requires valid settings for DB/auth-backed operations. Never publish it directly to the internet.

## Source map

`src/agent_control_plane/api.py` defines typed HTTP contracts; `auth.py` validates principals; `db.py` scopes connections and RLS; `memory.py` handles provenance and transitions; `migrate.py` applies ordered checksum-protected migrations; `personal_worker.py` and runtime adapters perform authorised work; `routing.py` governs compute/model decision logic; `terminal_client.py` is thin and intentionally not a login broker.

## Schema and contract rules

Never edit the body of an already applied SQL migration: checksums must remain stable. Add a new numbered migration and regression tests for roles, RLS, schema version compatibility, concurrent insert/replay and data isolation. Use scoped signed AgentPrincipal subject/tenant claims, not request-provided owner identity. Make background task states and cancellation observable.

## Integration design review

Before adding code ask: who owns canonical state? What trusted identity authorises the action? Which typed/versioned interface separates control plane from runtime/provider? What destructive restart or wrong-user test proves it? Do not create a new SDK/CLI when an existing Qiskit/PennyLane notebook or runtime adapter suffices.

Read [quick start](https://github.com/nyameko/agent-control-plane/blob/main/docs/QUICK_START.md), [ADR index](https://github.com/nyameko/agent-control-plane/tree/main/docs/adr) and [contribution rules](https://github.com/nyameko/agent-control-plane/blob/main/CONTRIBUTING.md).