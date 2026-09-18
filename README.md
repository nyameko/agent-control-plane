# agent-control-plane

Cross-project coordination for a self-hosted engineering and research organization.
The compute fabric can include OpenStack VMs, Kubernetes, Slurm, A100/H200 inference
and eventually QPUs. Models, agent runtimes, tools and resource schedulers remain
separate components with explicit authority.

**v0.2 implements one read-only administrative vertical slice.** An authenticated
private Django administrator submits a fixed Prometheus diagnostic. PostgreSQL
persists its task, run, evidence and events. A dedicated, persistent Hermes profile
explains the evidence without shell tools or Kubernetes credentials. The private
administrator page shows its history and failures.

These are source and deployment files, not evidence of a live deployment. Published
images, sealed credentials, a real model endpoint and cluster acceptance checks
are required before first use.

## Repository boundaries

| Repository | Owns |
| --- | --- |
| [infra-hpc-qc-k8s](https://github.com/nyameko/infra-hpc-qc-k8s) | Infrastructure desired state, Argo deployment, Cinder, network policy, resource schedulers |
| [quantum-platform](https://github.com/nyameko/quantum-platform) | Identity/programmes, researcher product, private admin and future personal conversation data |
| [quantum-workflows](https://github.com/nyameko/quantum-workflows) | Reproducible scientific workflows, runners and result provenance |
| **agent-control-plane** | Authorized tasks, agent runtime adapters, operational history, policy and future delegation |

The name avoids confusing the shared coordination service with the researcher
portal. A top-level administrative coordinator supervises bounded specialists;
it does not replace Terraform, Argo, Kubernetes, Slurm or their access controls.

## Start here

- [Phase 1 implementation and API contract](docs/12-phase1.md)
- [Deployment, secrets, validation and recovery runbook](https://github.com/nyameko/infra-hpc-qc-k8s/blob/main/docs/tutorials/10-agent-control-plane-phase1.md)
- [Spacemacs/gptel, Hermes, Herdr, Herder and Glyph review](docs/13-ade-workflow.md)
- [Repository integration review and staged future architecture](docs/14-integration-review.md)
- [Full documentation map](docs/README.md)

The runtime path is: private administrator → portal-signed identity → API →
PostgreSQL queue → fixed diagnostic → Hermes explanation → persistent history.
The API has no generic command, provisioning or workflow-execution endpoint.

## Source layout

| Path | Purpose |
| --- | --- |
| `src/agent_control_plane/api.py` | Authenticated administrative API and legacy authenticated planning |
| `auth.py`, `db.py`, `schema.sql`, `migrate.py` under that package | Identity verification, durable queue/ledger, enforced schema and migration |
| `diagnostic.py`, `worker.py`, `hermes_runtime.py` | One fixed tool, bounded worker, pinned Hermes adapter |
| `Dockerfile`, `Dockerfile.hermes` | API/migration and persistent worker images |
| `scripts/create_secrets.py` | Generate private local Secret files for kubeseal |
| `tests/` | Authentication, safe diagnostics, native PostgreSQL behavior and Hermes protocol/persistence |
| `configs/`, `contracts/v1/`, `routing.py` | v0.1 proposed broader catalogs and dry-run planning, not live scheduling |
| `migrations/0001_initial.sql` | Future-schema design reference; **not** the executable Phase 1 migration |

## Local validation

Use Python 3.12 for parity with the service images and CI.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check src tests scripts
pytest
```

Native PostgreSQL tests require disposable test DSNs; the pinned Hermes contract
test is opt-in with its SDK installed. See the Phase 1 document for both. CI runs
these gates before publishing ACP images. A local test without those dependencies
reports skips rather than silently substituting production guarantees.

To run the API, configure the database and JWT verification key as described in
the deployment document. `agent-control-plane` binds to loopback port 8080 by
default. `/health` is a process probe; `/ready` checks the database. Every task and
planning endpoint requires a valid portal assertion. Do not expose the API publicly.

## Persistent state

The control plane's PostgreSQL database owns administrative tasks, runs and audit
history. The portal owns user identities and a stable external UUID mapping.
Future personal chat/research memory belongs alongside platform user data, with
ACP runs referring to conversation IDs. Hermes retains its native session state
on a profile-specific Cinder PVC; its SQLite file does not replace user-data
PostgreSQL or the operational ledger.

One profile, one worker and one configured inference route are intentional Phase 1
constraints. The worker's reviewed identity/configuration is reseeded from the
image. Automatic learning and general tools are disabled. Each run gets a distinct
persistent session. Retained volumes protect against accidental lifecycle deletion;
backups and tested restore remain necessary.

## Next stages

Add more bounded diagnostics, then personal conversation APIs and persistent
portal/Jupyter clients. Follow with isolated repository work, reviewed mutation
paths and evaluated model/compute routing. Telegram/Discord should be authenticated
channel adapters. Herdr can supervise local and remote terminal agents today;
Herder is a separate optional CLI-job adapter, and Glyph adds developer naming
and fleet ergonomics. None is required in the Phase 1 execution path.

The architecture documents retained from v0.1 describe the wider ambition. The
v0.2 Phase 1 contract and integration review define what is currently implemented
and refine data ownership where that earlier proposal was broader.

## License

Apache-2.0.
