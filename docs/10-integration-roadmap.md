# 10. Integration roadmap

## 10.1 Sequencing principle

Build durable authority before broad autonomy.

~~~text
identity
  |
canonical conversation continuity
  |
memory
  |
projects
  |
skills
  |
runtime-native profile enrichment
  |
ubiquitous clients
  |
multi-runtime/meta-orchestration
  |
accelerated inference
  |
bounded engineering/scientific execution
  |
QPU orchestration
~~~

## 10.2 Foundation already established

The current repository family has established:

- immutable AgentPrincipal identity mapping;
- a Phase-1 ACP administrative API/worker/PostgreSQL slice;
- durable task/run/event history;
- bounded Hermes integration;
- ACP deployment/storage/network-policy resources;
- Quantum Platform workbench and Slurm execution foundations.

M4 starts from that foundation.

## 10.3 M4 — persistent personal agents

### M4a — Persistent Personal Agent

Goal: canonical conversation continuity.

Deliver only:

- minimal project stub;
- canonical conversation/messages;
- AgentPrincipal + tenant ownership/RLS;
- idempotent user-message ingestion;
- personal task/run lineage;
- worker context hydration from ACP;
- assistant response commit;
- survival across browser/Jupyter/SSH/worker/API restart;
- permanent automated destructive conformance test.

Do not add full memory, rich projects, skills or Paperclip.

### M4b — Memory

Durable memory + provenance + retrieval + correction/invalidation + lifecycle.

### M4c — Projects

Full research/engineering workspace model.

### M4d — Skills

Governed/versioned skills and scope bindings.

### M4e — Persistent Hermes Profiles

Rich runtime-native persona/profile/session persistence while ACP remains canonical.

### M4f — Quantum Platform Guide

Ubiquitous researcher-facing ACP agent UI.

### M4g — SSH Enterprise Client

Terminal attach/resume/create/list/run experience.

## 10.4 Multi-runtime ecosystem

After M4:

- Paperclip/meta-orchestration;
- Hermes + alternative runtime adapters;
- coding/security/storage/research/tutorial specialists;
- Herdr-integrated developer workflows;
- adapter conformance tests.

Every runtime must pass a portability requirement:

> The same ACP conversation can continue after replacing the runtime.

## 10.5 Accelerated inference

Then add:

- A100/H200 serving pools;
- vLLM production inference;
- local Ollama/llama.cpp specialist pools;
- model gateway;
- quotas/health/routing telemetry;
- evaluation-aware logical model pools.

## 10.6 Engineering execution

Then add controlled:

- sandbox broker;
- isolated worktrees;
- build/test workers;
- agent/* branch workflows;
- immutable patch/test evidence;
- exact-plan approval for mutations.

Protected branches/GitOps authority remain intact.

## 10.7 Scientific execution

Integrate ACP with Quantum Platform/quantum-workflows bounded execution contracts:

~~~text
CPU Slurm
   |
A100/H200
   |
multinode/MPI
   |
hybrid quantum-classical workflow stages
   |
QPU/provider/QRMI/QDMI
~~~

ACP records agent/runtime/task correlation. quantum-workflows owns scientific provenance. Slurm/provider owns scheduling state.

## 10.8 External channels and collaboration

Only after identity/context is stable:

- Telegram/Discord account linking;
- channel-scoped capabilities;
- notification/digest policy;
- collaboration discovery;
- programme/tutor/community agents.

## 10.9 Carefully bounded operations automation

Start with reversible low-risk actions.

Production Terraform apply, broad Kubernetes apply, account/security-group changes and protected-branch merge stay outside general agent authority unless a future ADR explicitly changes that with a risk model and break-glass path.

## 10.10 Release/conformance

A milestone is not complete because YAML exists.

Release evidence includes:

- commit SHAs;
- image digests;
- migration version;
- CI results;
- runtime/model revisions;
- acceptance/conformance results;
- rollback/recovery evidence.

Major releases follow the broader six-month platform rhythm with active dev/staging followed by release freeze/stabilisation.

## 10.11 Immediate M4a repository sequence

~~~text
agent-control-plane
  feature/m4a-persistent-personal-agent
  migration infrastructure
  canonical conversation tables
  ownership/RLS
  API/tests
  personal-turn runtime hydration
  destructive conformance test

quantum-platform
  feature/m4a-personal-agent
  researcher-scoped ACP assertion
  minimal project/conversation UI
  server-side ACP client

infra-hpc-qc-k8s
  feature/m4a-persistent-personal-agent
  migration rollout
  personal worker
  NetworkPolicy/telemetry
  restart/destruction acceptance runbook

quantum-workflows
  no required M4a change
~~~
