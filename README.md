# agent-control-plane

## Current milestone — M4 persistent agents

The infrastructure/platform stack now has a validated M3 path from authenticated research identity through a Jupyter workbench to durable Slurm execution. ACP's next job is therefore **persistence and continuity**, not broader autonomous infrastructure authority.

M4 must preserve the same project/conversation across portal, Jupyter, SSH/TUI and editor clients, surviving browser close, Jupyter Pod loss and agent-runtime restart.

See [M4 — Persistent Personal Agents](docs/M4-PERSISTENT-AGENTS.md) and [Quick Start](docs/QUICK_START.md).


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

## Jupyter workbench and execution clients

The normal research notebook is a cheap KubeSpawner workbench, not a standing HPC reservation. Agent Control Plane should treat portal, Jupyter and SSH as **clients of the same durable conversation/task services**.

```text
Portal          Jupyter workbench          SSH/TUI
  \                  |                     /
   \                 |                    /
      authenticated user/delegation
                 |
         Agent Control Plane
          /             \
   conversation       bounded tools
     state                |
                          +-> execution API / quantum-workflows
                          +-> diagnostics
                          +-> reviewed mutations
```

The agent may help choose a logical execution target such as `qiskit-aer-large`, explain cost/queue/fit, or submit a bounded authorized job through the platform execution API. It must not bypass entitlement policy or translate user intent into unrestricted raw scheduler access.

Notebook culling, pod restart or switching to SSH must not destroy the user's canonical conversation/memory. Runtime PVCs remain implementation state only; stable conversation IDs and user/programme memory remain platform data.

## Public topology policy

This repository may describe infrastructure **roles, trust boundaries and logical execution targets**, but it must not duplicate the authoritative live network map. Concrete internal CIDRs, fixed addresses, VPN peer mappings, provider IDs and environment node counts belong in protected `infra-hpc-qc-k8s` environment data. Public examples use semantic role names/placeholders instead.

## Public repository topology policy

Public documentation describes **roles, trust boundaries, interfaces and example topology**, not the authoritative live internal network map. Real CIDRs, fixed host addresses, VPN peer mappings, provider resource IDs and environment-specific routing belong in protected infrastructure inventory/private variables. Examples should use semantic placeholders such as `<MGMT_CIDR>`, `<K8S_API_VIP>`, `<SLURM_CONTROLLER_IP>` or private DNS abstractions rather than production addresses.
