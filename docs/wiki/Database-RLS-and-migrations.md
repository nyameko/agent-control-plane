# ACP PostgreSQL, row-level security and schema migrations

## Canonical ownership

ACP PostgreSQL owns private projects, conversations, messages, task/run references, memories and profile preferences. The user identity is the trusted Quantum Platform **AgentPrincipal UUID** with scoped tenant. A POSIX UID, SSH username or runtime-local SQLite database must never replace this canonical ownership.

`src/agent_control_plane/migrate.py` defines ordered, checksum-protected SQL migrations:
| Version | Purpose |
|---|---|
| 1 | initial ACP schema |
| 2 | persistent personal conversations |
| 3 | personal turn ledger |
| 4 | private memory and revision model |
| 5 | programme conversations/rooms |
| 6 | portable personal profiles |

The migration routine uses a PostgreSQL advisory transaction lock, validates installed checksums and refuses unknown versions or version gaps. **Never edit an already deployed SQL migration**; create a new numbered migration and provide forward/rollback compatibility evidence.

## Separate database privileges

A schema-owner credential runs migrations; the application role handles bounded API operations; a backup role has a distinct administrative lifecycle. The application should operate with row-level security enabled and **forced** where private data is stored. Transaction-scoped tenant/subject settings must not leak across pooled connections or be caller-controlled. Test wrong-tenant, guessed UUID, stale role, revocation and missing claims.

## Read-only runtime verification

On the authorized Kubernetes admin host, inspect the deployed image and Argo drift first. The repository's conformance runbook includes a read-only query using the *already configured application role* to list `acp1.schema_version` and check presence of `programme_conversation` (v5) and `personal_profile` (v6). Do not output database DSNs, passwords, memory bodies or user messages. `/ready` deliberately tolerates multiple schema versions; it is **not** proof that v5/v6 are live.

## Safe migration release process

1. Record exact source, migration checksum and candidate application image digest.
2. Perform backup and isolated restore checks.
3. Verify schema-owner permissions in a migration Job rather than an API Pod.
4. Run migrations in a controlled order; avoid app writes that assume new tables until ready.
5. Deploy compatible API/worker images through reviewed GitOps changes.
6. Exercise authenticated endpoint, tenant isolation, memory revision and programme-room negative tests.
7. Record observed image, schema and functional evidence for release acceptance.

Sources: [ordered migration implementation](https://github.com/nyameko/agent-control-plane/blob/main/src/agent_control_plane/migrate.py), [database scope implementation](https://github.com/nyameko/agent-control-plane/blob/main/src/agent_control_plane/db.py), [live conformance read-only procedure](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md), [state architecture](https://github.com/nyameko/agent-control-plane/blob/main/docs/05-memory-state-and-storage.md).