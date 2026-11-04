# API and data contracts

The following paths are declared in [`src/agent_control_plane/api.py`](https://github.com/nyameko/agent-control-plane/blob/main/src/agent_control_plane/api.py); supported behavior depends on the currently deployed schema, runtime and claims. Use Quantum Platform's proxy for normal browser clients rather than handling ACP signing keys.

| Domain | Representative FastAPI paths |
|---|---|
| Availability | `GET /health`, `GET /ready` |
| Admin | `POST /v1/plans/dry-run`, `/v1/admin/tasks` |
| Personal profile | `GET/PUT /v1/profile` |
| Projects | `GET/POST /v1/projects`, `GET/PATCH /v1/projects/{id}` |
| Conversations | `GET/POST /v1/conversations`, `GET/PATCH /v1/conversations/{id}` |
| Messages and runs | `POST /v1/conversations/{id}/messages`, `POST /v1/conversations/{id}/turns`, `GET /v1/runs/{id}` |
| Memory | candidate creation, approve/correct/revoke, private listing/retrieve under `/v1/memories` |
| Programme rooms | `/v1/programmes/{id}/conversations` and room message paths |

Validate methods, schemas and required headers from the source for each operation; do not assume every path supports full CRUD or that an HTTP 202 means the run has completed. Personal and programme scopes differ. Mutating operations require explicit permission, idempotency where defined and concurrency protection (for example revision match). A guessed resource ID belonging to another user must not reveal its existence.

## Data durability

Migrations are ordered from 1 through 6 in [`migrate.py`](https://github.com/nyameko/agent-control-plane/blob/main/src/agent_control_plane/migrate.py). PostgreSQL is canonical for project/message/memory/profile information; a Hermes SQLite session is not. Source versions and live versions must be checked separately. ACP run IDs, scheduler job IDs and science workflow run IDs are correlated, not made identical.

For detailed semantics read [minimal memory contract](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4b-MINIMAL-MEMORY-CONTRACT.md) and [programme authorization ADR](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0010-m4c-workspaces-programme-authorization.md).