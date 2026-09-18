# Phase 1: one read-only administrative vertical slice

This is the implementation contract for v0.2. It supersedes the v0.1 roadmap where
that roadmap described Phase 1 as a future HTTP integration. The implementation
uses a pinned Hermes Python adapter in a dedicated worker. It does not expose the
Hermes gateway or its general tool surface.

## What happens

```mermaid
sequenceDiagram
    participant Admin as Administrator
    participant Portal as Private Django admin
    participant API as Control-plane API
    participant PG as PostgreSQL
    participant Worker as Hermes worker
    Admin->>Portal: Submit fixed diagnostic, with CSRF
    Portal->>API: Short-lived signed identity + idempotency key
    API->>PG: Commit task, queued run, actor event
    API-->>Portal: Task UUID and status
    Worker->>PG: Claim queued run
    Note over Worker: Read fixed Prometheus metric; store evidence; ask Hermes to explain
    Worker->>PG: Commit evidence, explanation or failure
    Portal->>API: Read task and events
    API->>PG: Tenant-scoped history query
    Portal-->>Admin: Evidence, explanation, timestamps, status
```

One action reads `kube_pod_status_ready` for the `quantum-platform` namespace. Its
PromQL is compiled into `diagnostic.py`:

```promql
sum by (condition) (kube_pod_status_ready{namespace="quantum-platform"})
```

This reports counts of pod Ready conditions. It does not prove application health,
node health, scrape freshness, GPU availability, or quantum-provider availability.
Missing metrics produce `diagnostic_no_data`, never a healthy verdict. The tool
retains only known condition labels, finite integer counts and timestamps. It
rejects redirects, oversized replies, malformed data and non-success responses.
There is no input for PromQL, namespace, URL, shell command or model selection.

The worker invokes this deterministic tool once before inference. Hermes explains
the result with **zero callable tools**, a 1-iteration budget, a 1,200-token output
budget and a parent-enforced wall-clock timeout. The parent stores evidence before
starting inference. A model outage therefore produces a failed run with any
completed evidence still visible. This is a deliberately small agent harness; it
is not yet autonomous tool selection or provisioning.

## API and identity

| Endpoint | Access | Behavior |
| --- | --- | --- |
| `GET /health` | Internal probe | Process health only |
| `GET /ready` | Internal probe | Database version and non-bypass role check |
| `POST /v1/admin/tasks` | Signed administrator assertion | Enqueue the one allowed diagnostic |
| `GET /v1/admin/tasks?offset=0` | Same | Up to 50 tasks, newest first |
| `GET /v1/admin/tasks/{uuid}` | Same | Run, evidence, explanation, events |
| `POST /v1/plans/dry-run` | Same; body identity must match | Legacy planning only; no execution |

A task submission body is exactly:

```json
{"diagnostic":"quantum-platform-pod-readiness"}
```

The `Idempotency-Key` header is a UUID. Repeating it for the same authenticated
actor and tenant returns the existing task. A new key is required for a new
observation. Queue admission permits one active task per actor and at most twenty
per tenant. These are capacity limits, not a complete inference spending policy.

Django owns authentication and administrative membership. Its existing
`secure_admin_login`/allauth flow is preserved. All new views require active staff
membership, CSRF for submission, and the configured private admin hostname. This
change does not silently make MFA enrollment mandatory; it follows the site's
configured allauth policy. Do not infer MFA enforcement merely from MFA support.

`portal.AgentPrincipal` gives each participating User an immutable UUID, independent
of integer database IDs, usernames and email addresses. The portal signs a
60-second Ed25519 JWT with `iss=quantum-platform`, `aud=agent-control-plane`, that
UUID subject, the configured tenant and `scope=admin:diagnostics`. The API has only
the public verification key. The private signing key remains in the portal. It is
not a browser token, gptel credential, model key or Hermes secret.

The API accepts only EdDSA, verifies issuer/audience/timestamps, rejects lifetimes
over 90 seconds, and permits only the configured administrative tenant (`nyameko`
by default). No tenant or actor is trusted from a diagnostic body. Staff can see
that tenant's administrative run history, including other administrators' runs;
this endpoint is not a researcher-facing history API. Staff revocation takes
effect on newly issued assertions; an already issued token has up to 60 seconds
of residual validity, plus clock leeway. Later multi-tenant support needs an
explicit tenant-authorization contract, rather than broadening this scope.

## State and failure semantics

The installed executable migration is `src/agent_control_plane/schema.sql`, run by
`python -m agent_control_plane.migrate`. `migrations/0001_initial.sql` remains the
v0.1 future-schema proposal and **must not be applied** for this release. The
migration has a transaction, an advisory lock, a version and a checksum. Repeated
runs are safe; a changed historical schema fails and demands an explicit upgrade.

Three production tables form the slice: `acp1.task`, `acp1.run`, `acp1.event`.
They enforce foreign keys, allowed diagnostic/status values and tenant row-level
security. The application role is not an owner, superuser or `BYPASSRLS` role. Every
application transaction sets its tenant locally; the setting does not survive the
transaction. Missing tenant context grants no rows. The app can append and read
events but cannot update/delete them. This is append-only **for that role**; it is
not cryptographic tamper evidence against the database administrator.

The API commits before returning a task ID. PostgreSQL is the queue; there is no
in-memory queue, Celery/Redis dependency or request-bound background task.
A worker claims a row with a lock and commits `running` before starting work.
A singleton StatefulSet, Cinder RWO volume, profile file lock and PostgreSQL
advisory lock constrain the worker. Do not scale the worker replicas above one.

After a worker restart, abandoned `running` runs become terminal
`worker_interrupted` failures. They are not automatically repeated. A run may have
completed inference just before a crash without committing its answer. The record
honestly reports interruption; submit a new task if another observation is wanted.
This is not an exactly-once claim. Queued runs remain available after restart.
Native PostgreSQL concurrency tests are a required release gate.

Hermes uses one `HERMES_HOME=/var/lib/hermes/admin-readonly` profile. Each run has a
separate `acp-<run UUID>` session in its persistent `state.db`. Profile files and
logs survive pod replacement. PostgreSQL owns task/run/evidence/result history;
Hermes SQLite is runtime state, not the portal's canonical history database.
The worker reseeds reviewed `SOUL.md` and configuration from its image at startup.
Automatic learning, user-profile memory, project context, plugins and background
reviews are disabled for this initial administrative profile. Persistent does not
mean that every form of memory learning is enabled.

The Hermes subprocess receives the model credential and profile location, not the
PostgreSQL password or portal signing key. It is killed on timeout and on parent
execution errors. The pod has no Kubernetes token, cluster role, host mount,
privileged container, Docker socket or OpenStack credential. This pod is not an
appropriate sandbox for arbitrary untrusted code; there is no such tool here.

## Installation and validation

Use the deployment runbook in
[`infra-hpc-qc-k8s/docs/tutorials/10-agent-control-plane-phase1.md`](https://github.com/nyameko/infra-hpc-qc-k8s/blob/main/docs/tutorials/10-agent-control-plane-phase1.md).
It covers images, sealed secrets, Cinder, private admin activation, first sync,
backup, restart checks and rollback. Do not apply the unconfigured base directly.

For local source tests:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

Database tests intentionally skip unless `ACP_TEST_OWNER_DATABASE_URL` and
`ACP_TEST_DATABASE_URL` point at a **disposable native PostgreSQL database**. They
drop the `acp1` schema. The owner can create the test `acp_app` role; its test-only
password is `test-only`. Never point these test variables at a live database.
GitHub Actions provisions PostgreSQL 18 and runs the complete database suite,
including independent connection locking. It then installs the pinned Hermes
source editably and tests the actual adapter against a local streamed OpenAI
protocol fixture with `ACP_TEST_HERMES=1`. That fixture verifies protocol, empty
tool exposure and persisted runtime sessions; it does not evaluate a real model.

The API itself requires `ACP_DATABASE_URL`, `ACP_JWT_PUBLIC_KEY_FILE` and
`ACP_TENANT_ID`. The worker additionally requires `ACP_MODEL`,
`ACP_MODEL_BASE_URL` (OpenAI-compatible base including `/v1`), `ACP_MODEL_API_KEY`,
`ACP_PROMETHEUS_URL`, `HERMES_HOME`, and an optional 30–600 second
`ACP_RUN_TIMEOUT_SECONDS`. There is no default external provider or silent
fallback to a paid API. For an unauthenticated internal model server, supply an
explicit non-secret local placeholder key; protect the endpoint with network rules.

## What is not enabled

Provisioning, repository writes, Kubernetes API calls, shell tools, Slurm jobs,
QPU submissions, external messaging, user chat, persistent Jupyter widgets,
automatic model escalation, and a Herder broker remain later stages. These are
not hidden unfinished endpoints. The Phase 1 boundary is the fixed diagnostic.
