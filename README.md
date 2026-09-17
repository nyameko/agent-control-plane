# agent-control-plane

Policy-aware orchestration for a self-hosted virtual engineering and research organisation.

`agent-control-plane` coordinates people, specialist agents, agent runtimes, model servers,
tools, sandboxes and heterogeneous compute. It sits across the existing platform without
replacing the systems that already have authoritative control:

| Repository or system | Question it answers | Authority |
| --- | --- | --- |
| [`infra-hpc-qc-k8s`](https://github.com/nyameko/infra-hpc-qc-k8s) | Where and how does the facility run? | OpenStack, Terraform, Ansible, Kubernetes, Slurm, storage, networking and operations |
| [`quantum-platform`](https://github.com/nyameko/quantum-platform) | Who may use it, and through which experience? | identity, programmes, portal, JupyterHub UX, jobs and results |
| [`quantum-workflows`](https://github.com/nyameko/quantum-workflows) | What reproducible scientific work executes? | workflow code, runners, parameters, scientific provenance and tutorials |
| **`agent-control-plane`** | Who or what should reason, delegate, remember and request an action? | agents, conversations, routing, policy, approvals, delegation and agent audit |
| Kubernetes / Slurm / OpenStack / GitOps | What actually runs or changes? | deterministic scheduling, resource lifecycle and desired state |

The project name is deliberate. **Control plane** describes a cross-cutting decision and
coordination layer. **Platform** would overlap with `quantum-platform` and imply that this
repository also owns the researcher portal and application experience.

## The central idea

This is not one all-powerful super-agent. It is a hierarchy of bounded principals:

```text
Nyameko / platform administrators / researchers
                       │
         web chat · gptel · Jupyter · API
         Telegram · Discord (constrained)
                       │
                       ▼
              Agent Control Plane
        identity · policy · route · audit
                       │
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
     Infra          Research        Security
  orchestrator    orchestrator    orchestrator
        │              │               │
        └────── specialist agents ─────┘
                       │
             runtime / harness adapters
        Hermes · direct LLM · future harnesses
                       │
           model route       execution route
               │                   │
      Ollama / vLLM /       sandbox broker
      llama.cpp / APIs            │
               │        OpenStack · K8s · Slurm
          CPU / A100 / H200        │
                              CPU/GPU/QPU
```

The top-level administrative agent has broad *visibility* and delegation scope. It does not
receive an invisible bypass around branch protection, MFA, GitOps, Slurm, Kubernetes RBAC,
OpenStack policy or approval rules.

## What this first commit contains

This commit is an architectural foundation and an executable policy-routing nucleus:

- a repository ownership and integration model grounded in the existing projects;
- a versioned task, execution-plan and event contract;
- declarative catalogs for agents, capabilities, model pools and compute classes;
- a deterministic, testable baseline router that keeps model placement separate from workload
  execution placement;
- an HTTP API for health checks and dry-run planning;
- a proposed PostgreSQL schema for conversations, messages, tasks, runs, approvals, routing
  decisions, jobs, artifacts and immutable audit events;
- storage contracts for PostgreSQL, Cinder PVCs, object storage, Git and secrets;
- designs for persistent chat across `quantum.nyameko.com`, JupyterHub, Spacemacs/gptel,
  Telegram and Discord;
- threat model, observability/evaluation plan and an incremental integration roadmap.

It intentionally does **not** claim to provision production agents, deploy an autonomous
administrator, or select live GPU nodes. Those require the corresponding changes and acceptance
tests in `infra-hpc-qc-k8s` and `quantum-platform`.

## Invariants

1. **Agents propose; authoritative systems execute.** GitOps changes Kubernetes, Terraform changes
   OpenStack, Slurm schedules HPC/QPU work, and the platform identity service authorises users.
2. **Every action has a principal, tenant, purpose and audit trail.** No unattributed background
   automation.
3. **Model routing and execution routing are different decisions.** A Hermes pod can use an H200
   model while its tool runs in an isolated CPU VM and its scientific job runs through Slurm.
4. **External messages are untrusted input.** Telegram, Discord, papers, web pages, logs and tool
   output never become instructions merely because an agent can read them.
5. **High-impact mutations require approval.** Approval is scoped to an exact plan and expires;
   approving a conversation is not blanket authority.
6. **Persistent state has an explicit owner.** PostgreSQL is not a filesystem, Cinder is not the
   chat database, Prometheus is not an audit log, and Git is not a secret store.
7. **Logical capabilities, not hostnames.** Agents request `code-deep`, `sandbox-cpu-large` or
   `qpu-gate`; policy and resource managers resolve physical placement.
8. **Portable interfaces before framework loyalty.** Hermes is the first-class initial runtime,
   but runtimes and harnesses sit behind adapters and versioned contracts.

## Repository layout

```text
agent-control-plane/
├── configs/                 example agents, capabilities and logical resource catalogs
├── contracts/v1/            JSON Schemas shared by clients, runtimes and brokers
├── docs/                    architecture, boundaries, security and roadmap
│   └── adr/                 durable architectural decisions
├── migrations/              proposed control-plane PostgreSQL schema
├── src/agent_control_plane/ executable routing nucleus and HTTP API
└── tests/                   credential-free routing and policy tests
```

Production Kubernetes resources do not live here. This repository builds an application image;
`infra-hpc-qc-k8s` pins the image digest, supplies secrets/PVCs/policies and deploys it through
Argo CD.

## Quick start

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
agent-control-plane
```

Then request a dry-run plan:

```bash
curl -s http://127.0.0.1:8080/v1/plans/dry-run \
  -H 'content-type: application/json' \
  -d '{
    "subject": "django:user:1",
    "tenant": "nyameko-lab",
    "channel": "gptel",
    "domain": "infrastructure",
    "intent": "Analyse the Traefik ingress failure and propose a patch",
    "quality": "deep",
    "sensitivity": "internal",
    "mutation_requested": false
  }'
```

The response is a plan, not an execution. It names a logical agent, model pool, execution class,
approval requirement and the reasons for each decision.

## Initial integration sequence

1. Keep the isolated `hermes-orchestrator` VM in `infra-hpc-qc-k8s` as the out-of-band
   administrative/federation root.
2. Deploy this API and a PostgreSQL database/schema in Kubernetes through Argo CD.
3. Connect one Hermes runtime through its HTTP run API; keep all tools read-only.
4. Add the authenticated chat surface to `quantum-platform` and bind conversations to the Django
   user and research programme.
5. Reuse the same conversation API from a JupyterLab extension and Spacemacs/gptel.
6. Add a sandbox broker for isolated repository analysis and patch generation.
7. Add Telegram/Discord liaison services only after identity linking, audit and approvals work in
   the portal.
8. Add model and execution placement using measured capability/queue telemetry.

The complete plan is in [`docs/10-integration-roadmap.md`](docs/10-integration-roadmap.md).

## Documentation

- [Documentation map](docs/README.md)
- [Reference architecture](docs/02-reference-architecture.md)
- [Repository boundaries](docs/03-repository-boundaries.md)
- [Memory, state and storage](docs/05-memory-state-and-storage.md)
- [Model and compute routing](docs/06-model-and-compute-routing.md)
- [Clients, chat, Telegram and Discord](docs/08-clients-chat-telegram-discord.md)
- [Integration roadmap](docs/10-integration-roadmap.md)
- [Threat model](docs/11-threat-model.md)

## Upstream position

- Hermes is the initial full agent runtime because it already exposes programmatic HTTP/SSE,
  approvals, sessions, tools, memory, skills and subagents.
- vLLM is the target production serving tier for high-throughput A100/H200 inference; Ollama and
  llama.cpp remain valuable development and efficient/specialised runtimes.
- DeepSeek Harness is an experimental adapter until its developer-preview interfaces stabilise.
- Herder may be evaluated as a local/remote CLI-worker adapter, not as a replacement for Slurm,
  Kubernetes or this control plane.
- Heretic is model-engineering experimentation, not the memory or orchestration layer.

See [`docs/07-runtimes-harnesses-and-sandboxes.md`](docs/07-runtimes-harnesses-and-sandboxes.md)
for the exact boundaries.

## Status

**V0.1 architecture and routing nucleus.** No production mutation path is enabled.

## License

Apache-2.0.
