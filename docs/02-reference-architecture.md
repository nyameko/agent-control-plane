# 2. Reference architecture

## 2.1 Logical architecture

```text
┌──────────────────────────── Human and system clients ─────────────────────────────┐
│ quantum.nyameko.com │ JupyterLab │ Spacemacs/gptel │ Telegram │ Discord │ API    │
└──────────────────────────────────────┬────────────────────────────────────────────┘
                                       │ authenticated request / stream
                                       ▼
┌──────────────────────────── Agent control plane ──────────────────────────────────┐
│ API gateway │ identity context │ conversations │ policy │ approvals │ audit       │
│ task service │ planner/router │ delegation graph │ memory service │ event outbox  │
└───────────────┬─────────────────────────┬────────────────────────┬─────────────────┘
                │                         │                        │
                ▼                         ▼                        ▼
       runtime adapters           model gateway             execution broker
   Hermes │ direct model │    logical model pools      logical execution classes
   experimental harnesses      │       │       │        │        │        │
                │            Ollama  vLLM  llama.cpp  OpenStack  K8s    Slurm/QRMI
                │                                       sandbox   jobs    CPU/GPU/QPU
                └───────────────────────── events/results ──────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────── State plane ──────────────────────────────────────┐
│ PostgreSQL │ Cinder PVCs │ object/artifact store │ Git │ secrets broker │ metrics │
└───────────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Components

| Component | Responsibility | Explicitly does not own |
| --- | --- | --- |
| API gateway | authenticated task/conversation API, streaming, idempotency | user passwords, bot platform credentials |
| Conversation service | canonical conversation/message history and channel continuity | model-specific scratch state |
| Policy decision point | capabilities, sensitivity, tenancy, approval and egress decisions | Kubernetes or Slurm placement |
| Planner/router | chooses logical agent, runtime, model pool and execution class | physical GPU/node selection |
| Runtime adapter | translates portable tasks/events to Hermes or another harness | global identity or policy |
| Model gateway | logical model names, rate/usage limits, health/fallback | tool execution |
| Execution broker | creates signed, bounded requests for a sandbox, K8s job or Slurm job | scheduling algorithms owned by those systems |
| Memory service | retrieval and promotion of authorised long-term context | automatic retention of every message forever |
| Approval service | exact plan digest, approver, expiry and outcome | applying the approved action itself |
| Audit service | append-only security and operational event history | high-cardinality monitoring dashboards |

## 2.3 A request end to end

1. A client obtains the user's established `quantum-platform` session or a short-lived delegated
   token.
2. The control plane resolves subject, tenant/programme, channel, sensitivity and allowed
   capabilities.
3. A task record is created before model execution so failure remains visible.
4. The deterministic policy layer constrains candidate agents, models, tools and execution classes.
5. A planner may rank the remaining candidates. The selected plan and reasons are persisted.
6. A runtime adapter starts or resumes an agent session using the exact agent-definition digest.
7. Tool requests return to the policy layer. The runtime never obtains a generic privileged shell.
8. Read-only calls may execute directly. Mutations pause on an exact approval request.
9. Approved execution is submitted to the appropriate authoritative system.
10. Events stream to every attached client; results and artifacts are persisted by type.
11. A final response links evidence, tests, job IDs, artifacts and unresolved risks.

## 2.4 Administrative root outside the managed cluster

The existing isolated `hermes-orchestrator` VM remains valuable as an out-of-band federation and
reporting root. A Kubernetes failure must not erase the only path used to diagnose Kubernetes.

That VM should run a narrowly scoped administrative Hermes profile and control-plane client. The
multi-user API, conversations, channel adapters and ordinary research agents run inside Kubernetes.
The out-of-band root consumes replicated status and can request bounded recovery workflows; it is
not a second source of user conversation truth.

## 2.5 Availability and failure domains

- If H200 inference is unavailable, the router may fall back only to a pool permitted by policy.
- If the agent runtime fails, the canonical task/run state remains in PostgreSQL.
- If PostgreSQL is unavailable, new stateful work stops rather than silently becoming anonymous.
- If Kubernetes is unavailable, the isolated administrative root still reports infrastructure
  health, but normal multi-user sessions degrade.
- If Telegram or Discord is unavailable, web/Jupyter/gptel conversations continue unchanged.
- If an execution worker dies, its lease expires and the broker reconciles the job idempotently.

## 2.6 Initial deployment topology

```text
isolated OpenStack VM
└── administrative Hermes federation root

Kubernetes namespace: agent-control-plane
├── API / policy / routing replicas
├── worker replicas
├── Hermes runtime profiles
├── Telegram adapter
├── Discord adapter
└── network policies

PostgreSQL
└── separate database and credential for agent-control-plane

Cinder
├── runtime profile PVCs
└── per-user or per-project workspaces where justified

Slurm / OpenStack
└── execution targets reached only through brokers
```
