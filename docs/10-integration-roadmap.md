# 10. Integration roadmap

## 10.1 Sequencing rule

Build one secure vertical slice before a broad catalogue of agents:

```text
identity → conversation → read-only Hermes → evidence → audit → sandboxed patch → approval
```

Only then add external chat, autonomous schedules, more harnesses and production mutations.

## Phase 0 — repository and contracts (this commit)

### `agent-control-plane`

- establish name, boundaries, threat model and ADRs;
- define V1 task/plan/event contracts;
- define agent, capability, model and execution-class catalogs;
- implement/test deterministic dry-run routing;
- propose relational schema and cross-repository changes.

### Acceptance

- no secret or production credential;
- tests pass without model/GPU/network;
- plans explain independent model and execution routing;
- mutation routes require approval and execute nothing.

## Phase 1 — read-only administrative vertical slice

### `infra-hpc-qc-k8s`

- complete and harden the isolated `hermes-orchestrator` VM;
- deploy `agent-control-plane` API/worker and PostgreSQL database through Argo CD;
- create Cinder PVC for one Hermes administrative profile;
- add NetworkPolicies and internal TLS/ingress;
- deploy one self-hosted model endpoint and logical model gateway;
- expose narrow read-only Prometheus, Kubernetes and Slurm tools;
- add ServiceMonitor/dashboards and backup policy.

### `quantum-platform`

- add immutable subject UUID;
- add a delegated-token endpoint for the control plane;
- add an administrator-only task/run viewer;
- link control-plane audit summaries into the existing audit UI.

### `agent-control-plane`

- implement PostgreSQL persistence, outbox worker and Hermes adapter;
- support start/status/events/stop for read-only runs;
- persist runtime/model decisions and tool evidence;
- implement capability checks at each tool boundary.

### Acceptance

- investigate cluster health without write credentials;
- restart Hermes/API pods without losing canonical task history;
- remove H200 endpoint and observe policy-valid fallback or explicit failure;
- prove untrusted log text cannot request a tool action;
- correlate one request across portal, Hermes and telemetry.

## Phase 2 — persistent user assistant

### `quantum-platform`

- shared Astro chat component for portal pages;
- conversation list/search/archive/export and retention settings;
- programme/tenant selector;
- attachment/context reference flow;
- JupyterHub launch linkage and JupyterLab extension configuration;
- approval UI foundation, still read-only in production.

### `agent-control-plane`

- conversation/message APIs and SSE stream;
- user/project agent instances and quotas;
- memory-candidate, consent/promotion and deletion flow;
- user-agent Cinder profile/workspace allocation metadata;
- logical presets for tutor, research and coding assistance.

### `.spacemacs.d`

- authenticated control-plane/Hermes backend;
- direct model gateway backend;
- `@quick`, `@infra`, `@quantum`, `@research`, `@review` presets;
- credentials from `auth-source`;
- explicit conversation binding command.

### Acceptance

- start in portal, continue in Jupyter and resume in gptel;
- notebook pod deletion does not lose conversation history;
- one user cannot enumerate another user's conversations/profile PVC;
- memory export/delete is demonstrable.

## Phase 3 — safe engineering work

### `infra-hpc-qc-k8s`

- sandbox broker and ephemeral 32/64-vCPU OpenStack worker profiles;
- egress filtering, image allowlist, quotas and cleanup reconciliation;
- read-only Git integration, then narrowly scoped `agent/*` branch push;
- isolated test Kubernetes/Slurm targets for integration tests.

### `agent-control-plane`

- repository/worktree tool adapter;
- immutable plan/diff/test artifact bundle;
- plan-bound approval with expiry and WebAuthn re-authentication;
- multi-agent review: implementer, tester, security reviewer, synthesiser;
- runtime/harness conformance test suite.

### Acceptance

- produce coordinated patches across the three core repositories;
- prove no agent can push `main`, merge, or access unrelated repositories;
- revoke approval when a diff or command changes;
- destroy a sandbox and retain only declared artifacts/audit.

## Phase 4 — model and compute fabric

### `infra-hpc-qc-k8s`

- vLLM pools on A100/H200 with reserved capacity and health telemetry;
- Ollama/llama.cpp development and specialist pools;
- model gateway authentication, quotas and fallback policy;
- Slurm execution adapter for CPU/A100/H200 and later QPU brokers;
- separate inference and research workload accounting.

### `agent-control-plane`

- live catalog resolution, queue/health-aware routing;
- evaluation registry and model/harness scorecards;
- budget and deadline constraints;
- execution leases, heartbeats, retries and reconciliation;
- capability-based scientific job planning.

### `quantum-workflows`

- machine-readable workflow descriptors;
- correlation ID input and manifest link;
- resource/capability requirements per stage;
- immutable runner digests and Slurm DAG acceptance tests.

### Acceptance

- CPU/A100/H200 selection matches measured requirements;
- QPU queue does not hold a GPU allocation;
- restricted tasks never leave self-hosted pools;
- route/fallback reasons are visible to users and operators.

## Phase 5 — Telegram and Discord

- deploy isolated liaison adapters;
- implement portal-generated one-time account linking;
- add DM/project-channel bindings and revocation;
- add status, digest and read-only task flows;
- require portal deep-link + WebAuthn for high-impact approval;
- enforce quiet hours, rate limits and privacy-safe group behaviour.

### Acceptance

- an unlinked account learns nothing about platform state;
- display-name collision cannot bind identities;
- bot compromise yields no infrastructure credential;
- private responses never leak into a project/public channel.

## Phase 6 — research intelligence and UY activation network

- literature ingestion with provenance/licence metadata;
- user/programme research graphs and saved searches;
- collaboration suggestions using consented, shareable summaries;
- experiment-to-literature feedback loop;
- UY activation/tutor agents with read-only open materials;
- SCC tutor mode respecting assessment and hands-off rules;
- multilingual and bandwidth-conscious clients where practical.

### Acceptance

- every collaboration suggestion explains evidence and sharing scope;
- private proposal contents are not used outside the tenant;
- tutor agents distinguish instruction from assessed work policy;
- research insights link to reproducible workflows/results.

## Phase 7 — carefully bounded operations automation

Begin with reversible, low-risk, pre-authorised runbooks such as restarting a failed development
pod or rotating a disposable sandbox. Expand only after measured reliability and incident review.

Production Terraform apply, cluster-wide Kubernetes apply, account/security-group changes and
protected-branch merge remain outside general agent authority. If ever enabled, each requires a
separate ADR, risk analysis, break-glass path and environment-specific approval policy.

## 10.2 Near-term pull request sequence

1. Create GitHub repository from this tarball and protect `main`.
2. Add database persistence and migration tooling here.
3. Add `agent-control-plane` namespace/database/PVC/network policy in `infra-hpc-qc-k8s`.
4. Add immutable subject and delegated-token endpoint in `quantum-platform`.
5. Add Hermes adapter with only health and read-only run APIs.
6. Add the portal's administrator run viewer.
7. Add one Prometheus health tool and its injection test suite.
8. Add personal persistent chat after the slice is reliable.

This ordering deliberately creates evidence and boundaries before granting “hands.”
