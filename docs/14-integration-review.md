# Integration review and future trajectory

Review date: 2026-09-17. This review distinguishes repository code, planned
architecture, and deployment evidence. Reading a manifest is not evidence that
its resource is running in the target cluster.

## Baselines

| Repository | Baseline | Concrete integration seam |
| --- | --- | --- |
| `agent-control-plane` | `ed856e2b6376db83531277718e67769677fa100c` | Architecture/dry-run nucleus; now extended with the bounded service slice |
| `infra-hpc-qc-k8s` | `9c552eadc3cff3c9e95e891f0833980a53156725` | Argo resources, Cinder CSI, monitoring, private admin ingress, Hermes VM foundation |
| `quantum-platform` | `56583da9dd5bba96c6f14b065125050bee87b369` | Django/allauth identity, programmes, private admin, existing migration/image workflows |
| `quantum-workflows` | `c2d4790ae0c3ad123dc4ca1a34d99e11a652f445` | Reproducible workflow runners and scientific result manifests |
| `.spacemacs.d` | `2151eddd71cd5f27010d049d66653c1d01060b4f` | Existing llm-client/gptel layer and workstation development experience |

The earlier review also inspected `uyuyu.africa` at `68787fc` and
`chpc-tech-eval/scc` at `0d585e4`; see `REPOSITORY-REVIEW.md`. This phase does not
modify their deployments or grant their users administrative access. The newer
identity/programme patch discussed separately is not present in the reviewed
quantum-platform main commit. This patch adds one independent identity table and
new admin views without rewriting programme approval or account registration.
Rebase and check migrations if that separate patch lands first.

| Upstream | Reviewed source revision |
| --- | --- |
| Hermes | `a566d20d226a8e2ef0747639dc8a3fc1c43f9dba` |
| Herdr | `101ccc20d3c6483a38ed9e0a1239b2ab908b1704` |
| Herder | `994f76c180ba5fbf76c5df38944e0619bbad5cc0` |
| Glyph | `7bb49bea4179fa6e28a55430a73dc2eb8e2aaf23` |
| gptel | `ecc693d69e0f9737fa637abc88ec4ce0c3187b8e` |

Hermes is pinned in the worker image. The other upstreams are reviewed integration
options, not bundled production dependencies. The Spacemacs layer uses the gptel
package provided by the user's existing llm-client layer; upgrades remain the
workstation's package-management responsibility.

## Repository authority

Keep `agent-control-plane` as a sibling repository. Its name captures a shared
coordination and policy service while `quantum-platform` remains the researcher
product. Infrastructure still owns desired deployment state, not application
source; workflows still own scientific computation, not agent chat.

The infra repository's dedicated `hermes_orchestrator` VM role currently prepares
a service user, directories and a safety policy. It does not demonstrate a running
multi-agent service. Preserve that VM as the future out-of-band administrative
entry point: it can remain reachable if Kubernetes fails. Phase 1 runs the bounded
worker in Kubernetes for a small, observable deployment. Do not run a second copy
of the same profile on the VM, mount one Cinder RWO volume from both places, or
have two independent orchestrators consume the same tasks without a lease contract.

The eventual infrastructure organization can contain an architect/coordinator,
OpenStack/Terraform, network/HAProxy/WireGuard, Kubernetes/GitOps, Slurm, storage,
observability and security specialists. Each has a separately declared tool and
credential scope. The top-level coordinator routes and reviews evidence. It must
not acquire the union of every specialist's credentials by default. Kubernetes
and Slurm remain the authorities for their resources, and Terraform/Argo remain
the paths for reviewed desired-state changes.

The current portal deliberately removes public `/admin` ingress and uses private
`admin.quantum.nyameko.com` with allauth login. The Phase 1 patch preserves that
boundary and adds a host check. There is no new public ACP ingress, no bearer key
in browser JavaScript, and no cross-database join from Django into the agent ledger.
The integration component is enabled only after its signing Secret and compatible
portal image/migration exist.

## State ownership and Cinder

| Data | Canonical owner | Storage / access |
| --- | --- | --- |
| User account, programme membership, administrative status | quantum-platform | Existing PostgreSQL; one immutable AgentPrincipal UUID |
| Administrative task/run/evidence/events | agent-control-plane | Dedicated PostgreSQL database, tenant RLS, restricted app role |
| Future personal chat, research memory, searches and saved queries | quantum-platform user-data service | User/programme-scoped PostgreSQL tables alongside user data |
| Future scientific job records | quantum-platform + authoritative scheduler | PostgreSQL metadata and scheduler/provider job identifiers |
| Workflow result manifests and large scientific artifacts | quantum-workflows / artifact service | Versioned manifests and durable object/project storage |
| Hermes native sessions, caches, runtime state | One runtime profile | Its own retained Cinder-backed RWO PVC |
| Reviewed SOUL, skills, tool definitions and model policy | Respective Git repositories | Immutable published versions mounted or seeded into profiles |
| Keys/tokens | Secret management | Sealed Secrets for deployment; credentials mounted only to their owner |

This refines the broader v0.1 schema proposal: a future user's portal conversations
and memories should live with the user's platform data as requested. The control
plane keeps operational runs and references conversation/message IDs. Do not
create two competing canonical chat histories or move the user's identity into
Hermes SQLite. Shared physical PostgreSQL hosting can be considered later, with
separate roles/schemas/databases and a tested migration. Phase 1 uses a separate
PostgreSQL instance to avoid changing privileges or reliability of the live
registration/programme database while introducing the service.

Cinder supplies durable block volumes. It does not replace SQL transactions,
identity controls, backups or memory ownership. RWO is not a shared filesystem:
a portal pod, Jupyter pod and Hermes pod on different nodes cannot all mount one
ordinary RWO claim for seamless history. Use authenticated data APIs for shared
history. Use object storage or an explicitly provisioned shared filesystem for
large shared artifacts. A retained PVC/PV reduces accidental data deletion; it is
not a backup, nor evidence of encryption. Verify the actual OpenStack encrypted
volume type and restore procedure before promising those properties.

Administrative telemetry, personal research memory and cohort tutoring memory
must not share an unrestricted vector index or profile. Retrieval needs tenant,
user/programme, provenance, consent/purpose, retention and deletion boundaries.
A student's contributed skill is untrusted code until reviewed and published.
Persistent prompts called SOUL do not grant authority: permissions belong to the
service/tool credentials and policy checks.

## Staged roadmap with acceptance gates

| Stage | Deliverable | Gate before expansion |
| --- | --- | --- |
| 1 | Fixed diagnostic, persistent run ledger/profile, private admin history | Native PostgreSQL CI, images, real model smoke test, Cinder restart and restore checks |
| 1b | More separately bounded diagnostics; read-only infrastructure specialists | Per-tool contracts, failure tests, telemetry redaction and least-privilege access |
| 2 | Personal conversation service and persistent portal chat panel | Stable subject/tenant authorization, pagination/streaming, deletion/export and data isolation tests |
| 2b | JupyterHub/JupyterLab and gptel conversation clients | Same conversation IDs, server-side delegated identity, authenticated event reconnect and cancellation |
| 3 | Repository engineering in isolated worktrees/sandboxes | Egress/credential/resource limits; versioned artifacts; patch review; trusted CI |
| 4 | Controlled infrastructure changes and scientific job submission | Exact-plan approvals, scheduler quotas, idempotency, rollback and reconciliation |
| 5 | Evaluated model/harness/compute routing and federation | Measured quality/latency/cost, placement constraints, tenant budgets and failure fallbacks |
| 6 | Research collaboration, tutoring, community interfaces | Consent-aware scheduled research, provenance, notification controls and institution-specific policy |

A stage is not complete because its YAML exists. Keep a release record with commit
SHAs, image digests, migration version, successful test evidence and live acceptance
results. Cross-repository work should be coordinated by a change-set ID and
compatibility table. Roll out compatible API changes before clients that depend
on them; preserve rollback windows rather than attempting an atomic merge across
independent repositories.

## Seamless portal, Hub and notebook assistance

A persistent chat panel is feasible in the portal shell and as a JupyterLab
extension/sidebar. The product should preserve a conversation ID and user-selected
research/programme context when moving between those surfaces. Authentication is
re-established through the approved platform/JupyterHub identity flow; never put a
platform signing key, broad Hermes API token or administrator credential in a
notebook, URL, localStorage or extension bundle. Use a backend-for-frontend and
short-lived, scoped delegation to the user-data conversation service.

Messages, memory references, search requests and research objects live in
PostgreSQL with the user/programme data. Runs reference those IDs. Streamed output
uses resumable event IDs; reconnects must not execute duplicate jobs. A visible
conversation can continue while its model or execution backend changes, provided
that authorization, context provenance, and compatibility are preserved. The UI
can hide hardware placement by default while retaining an inspectable record of
which model, tools, compute class and costs were used.

The shared administrative profile in Phase 1 must not become the personal agent
for every user. Introduce per-user or explicitly shared programme profiles and
retrieval policy before enabling persistent private conversations. Oversight can
start with status, resource usage, provenance and policy violations. Access to
private research content should be a separate, logged administrative capability.

## Model, harness and placement decisions

An agent's CPU service, inference server and tool/scientific job are separate
placements. A small Hermes process on a VM/pod can reason through H200 inference
and submit a CPU job to a 64-vCPU sandbox. An A100 service can answer interactive
requests while H200 capacity is reserved for measured deep/concurrent work.
The laptop remains a capable client and a valid local agent host.

Use logical model capabilities (`code-fast`, `research`, `reasoning`) above an
inference gateway, then bind them to reviewed deployed models. Parameter count
alone is not a scheduler: quantization, KV-cache/context length, batch size,
latency target, model quality, available memory, topology and concurrency all
matter. Benchmark candidate workloads before encoding the mapping. MIG partitions
are concrete resource profiles, not interchangeable fractions of an arbitrary GPU.
Do not let Kubernetes and Slurm independently allocate the same physical GPUs.

The initial route is explicit and fixed through `ACP_MODEL` and
`ACP_MODEL_BASE_URL`. It can target vLLM, Ollama or llama.cpp's compatible API.
There is no autonomous choice of H200/A100/VM or automatic external provider
fallback in Phase 1. Future routing should record reasons and enforce hard
privacy/quota/placement constraints before quality/cost optimization. Infrastructure
provisions inference pools; the model gateway routes requests; resource schedulers
place pods/jobs. An LLM can propose a route, but deterministic policy must validate it.

Hermes is the first runtime adapter. Herdr is terminal supervision, Herder an
optional CLI-job adapter, and DeepSeek Harness a future separately evaluated
runtime. Heretic belongs to model-weight experimentation, not memory storage or
orchestration. Keep model provenance and evaluations for modified weights as for
any other model.

## Telegram, Discord, collaboration, SCC and UYUYU

Telegram/Discord should be channel adapters into the same authorized task and
conversation services. They can be convenient for notices and bounded status
requests while the backend remains private. Use an explicit account-link flow,
platform tenant membership, per-channel allowed capabilities, replay protection,
rate limits and a policy for how much telemetry may leave the private platform.
A username, server role or private chat alone is not proof of a platform account.
Keep privileged changes and sensitive details in the authenticated portal.

A research-collaboration agent can periodically identify papers, calls and possible
collaborators, retain cited evidence and user preferences in the user's platform
data, and present candidates. Sending email/messages or invitations requires a
separate permission. Discovery does not authorize outreach. Keep organizational
memory separate from private researchers' unpublished work.

SCC and UYUYU can later use tutoring, translation, mentor assistance and programme
agents with cohort-specific budgets and assessment rules. They should consume
scoped shared platform services or run isolated deployments. They should not
inherit the infrastructure administrative tenant or its credentials. The
scientific differentiator remains reproducible hybrid workflows and usable access
to compute, not the number of agent frameworks chained together.
