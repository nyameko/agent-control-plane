# Agent Control Plane

**One durable research and engineering context, many clients, agents, runtimes, models and compute targets.**

Agent Control Plane (ACP) is the policy-aware coordination and state layer for a self-hosted research and engineering platform spanning Quantum Platform, Jupyter, SSH, editors, agent runtimes, open-weight models, Kubernetes, Slurm, GPUs and eventually QPUs.

Its central promise is simple:

> A researcher should be able to begin work in one surface, continue from another, change the agent runtime or model underneath it, lose a notebook Pod or agent worker, and still return to the same authorised project, conversation, memory, skills and execution history.

ACP exists to make that continuity independent of any particular model, vendor, client, harness or scheduler.

## Why this project exists

Modern agent systems tend to blur several different concerns:

- user identity;
- conversation history;
- long-term memory;
- agent runtime state;
- model selection;
- tool permissions;
- workflow execution;
- infrastructure scheduling;
- audit and scientific provenance.

That is convenient for a demo and dangerous for a long-lived research platform. If a runtime-specific SQLite file becomes the only copy of a conversation, replacing the runtime becomes a migration project. If a model name is embedded into every agent definition, replacing weights changes the application. If an agent receives raw infrastructure credentials, a prompt becomes an IAM boundary.

ACP deliberately separates these concerns.

~~~text
Clients
Quantum Platform | Jupyter | SSH/TUI | gptel | API | future channels
                              |
                              v
+------------------------------------------------------------------+
|                    AGENT CONTROL PLANE                           |
|                                                                  |
| identity context | projects | conversations | memory | skills    |
| tasks/runs       | policy   | approvals     | audit  | routing   |
|                                                                  |
|                  canonical durable context                       |
+----------------------+----------------------+--------------------+
                       |                      |
                       v                      v
             runtime / harness layer     execution contracts
             Hermes                  ->  Kubernetes
             LangGraph               ->  OpenStack sandboxes
             Letta                   ->  Slurm CPU/GPU
             PydanticAI              ->  quantum-workflows
             Agent Framework         ->  QPU/provider brokers
             OpenHands / Goose
             smolagents / others
                       |
                       v
                  model gateway
             vLLM | Ollama | llama.cpp
                       |
                       v
             open or external models
~~~

The runtime is replaceable. The model is replaceable. The client is replaceable. The compute target is replaceable.

**The authorised context is not.**

## Guiding philosophy

ACP is built around a small set of non-negotiable principles.

### Canonical state must have one owner

Conversation history, project bindings, durable memory, skill enablement and task/run history need a single canonical representation. Runtime-local caches and session databases may accelerate or enrich execution, but they must never be the only copy.

### Intelligence is replaceable; context is durable

Hermes is the first runtime, not the definition of the platform. Open-weight families, commercial APIs, runtime frameworks and coding agents will change. ACP must preserve the user's context across those changes.

### Identity is not a Unix number

Quantum Platform owns human identity. Each user has an immutable AgentPrincipal UUID used by ACP as the stable external subject. POSIX UID/GID belongs to the execution environment and is linked to that identity; it is not the user's ACP primary key.

### Policy lives outside the model

A system prompt, SOUL file or friendly agent persona is not an access-control mechanism. Capability checks, tenant/user isolation, approvals, secret resolution, scheduler quotas and execution policy are enforced outside the model.

### Schedulers remain authoritative

ACP does not reimplement Kubernetes, Slurm, OpenStack or QPU scheduling. It submits bounded, policy-checked work to those systems and records the resulting identifiers and evidence.

### Evidence beats confidence

Agent claims should be backed by tool results, tests, provenance, model/runtime revisions and execution records. Scientific results remain owned by quantum-workflows and their reproducibility contracts.

### Small vertical slices before broad autonomy

A narrow end-to-end capability that survives failure is more valuable than a catalogue of half-integrated agents. M4a therefore proves one persistent personal-agent path before memory, skills, multi-agent orchestration or accelerated inference expand.

### Open, portable and self-hostable by default

The platform should work with open standards, open interfaces, open weights and self-hosted infrastructure wherever practical, while allowing explicitly authorised external services when useful.

### Research capability should scale without changing the user model

The same identity and project should be usable from a modest workstation, a Kubernetes workbench, national HPC infrastructure, A100/H200 resources and later remote QPUs.

## Objectives

ACP is intended to provide:

1. durable cross-surface project and conversation continuity;
2. explicit memory, skill and project ownership with provenance;
3. interchangeable agent runtimes and harnesses behind portable contracts;
4. logical model pools independent of specific model names and weights;
5. bounded tool and execution capabilities rather than ambient credentials;
6. observable task/run/delegation history;
7. safe human approval for high-impact mutations;
8. model, runtime and compute evaluation without vendor lock-in;
9. integration with reproducible scientific workflows;
10. a foundation for a self-hosted virtual engineering and research organisation.

## What ACP is not

ACP is not:

- a Kubernetes, OpenStack or Slurm scheduler;
- a model server;
- the Quantum Platform login/user database;
- a replacement for quantum-workflows scientific provenance;
- a single giant agent prompt;
- a shared privileged shell;
- a requirement that every agent use Hermes;
- a requirement that every model run locally;
- a second GitOps authority;
- a licence for autonomous production mutation.

## Repository family and authority

| System | Canonical responsibility |
| --- | --- |
| infra-hpc-qc-k8s | OpenStack, hosts, Kubernetes, Cinder, networking, security controls, GitOps deployment, observability and Slurm infrastructure |
| quantum-platform | human identity, AgentPrincipal, programmes, entitlements and researcher-facing product experience |
| agent-control-plane | canonical agent projects/conversations/memory/skills, task/run history, runtime mappings, policy, approvals and agent orchestration contracts |
| quantum-workflows | reproducible scientific workflows, runner definitions, provider integration and scientific result provenance |
| Kubernetes / Slurm / QPU providers | physical execution and scheduling authority |
| Git repositories | reviewed definitions, policies, skills and source history |

This separation is architectural, not merely organisational.

## Identity model

The durable join is:

~~~text
Quantum Platform user
        |
        +-- AgentPrincipal UUID  <--- stable application identity
        |
        +-- Person / programme memberships
        +-- POSIX UID/GID        <--- execution identity
        +-- SSH keys
        +-- WireGuard identity
~~~

ACP stores the stable external subject derived from AgentPrincipal. It does not derive identity from username, email address, Django integer IDs or POSIX UID/GID.

## Canonical context

A future agent turn is assembled from ACP-owned state rather than whatever a runtime happened to remember:

~~~text
AgentRunContext
├── subject / tenant / programme context
├── project
├── conversation transcript
├── authorised retrieved memories
├── enabled skill versions
├── task/run lineage
├── capability grants
├── runtime profile reference
├── logical model pool
└── correlation / execution references
~~~

A runtime receives that context through an adapter and returns normalised messages, events, tool requests, artifacts, memory candidates and usage metadata.

This is the mechanism that keeps context correct when the runtime, model or client changes.

## Runtime and harness agnosticism

Hermes, together with its surrounding experimentation ecosystem, is the first runtime path. It is not the only permitted architecture.

ACP is designed to support adapters for stateful and workflow-oriented systems such as:

- Hermes;
- LangGraph;
- Letta;
- PydanticAI;
- Microsoft Agent Framework;
- Hugging Face smolagents;
- OpenHands;
- Goose;
- bounded coding-agent clients and future specialist runtimes;
- simple ACP-native workers where a full framework is unnecessary.

A runtime may have excellent persistence, memory or orchestration of its own. ACP still remains the canonical platform state and policy authority.

## Paperclip and meta-orchestration

Paperclip is a planned meta-harness/meta-orchestration layer, not the source of truth.

Conceptually:

~~~text
                    Paperclip
            coordination / meta-routing
                        |
                 Agent Control Plane
            canonical state + policy
                        |
       +----------------+----------------+
       |                |                |
     Hermes          OpenHands         Letta
     Heretic*        Goose             LangGraph
                     PydanticAI        Agent Framework
                     smolagents        other adapters
~~~

*Heretic belongs to controlled model-weight experimentation and evaluation rather than being a canonical memory or identity system.

Paperclip may decide which specialist/harness should work on a task. ACP decides what context and capabilities that work receives and records what happened.

## Models and inference

Agents request logical model service classes rather than hard-code a specific model:

- fast-local;
- general-balanced;
- deep-reasoning;
- coding;
- vision;
- long-context;
- research;
- restricted-local.

Those pools may resolve to self-hosted open-weight families or authorised external providers. The serving layer may use vLLM, Ollama, llama.cpp or another compatible runtime.

Changing the resolved model must not change the principal UUID, project UUID, conversation UUID, memory identifiers, skill bindings or historical run record.

## Current implementation and current milestone

The repository already implements a deliberately narrow Phase-1/v0.2 administrative slice:

~~~text
private Quantum Platform admin
        |
        v
short-lived signed identity
        |
        v
ACP API -> PostgreSQL task/run/event ledger
        |
        v
bounded diagnostic -> Hermes explanation
~~~

That slice proves identity delegation, database isolation, durable run history and a bounded Hermes adapter. It does not imply that the broader architecture is already deployed.

The next product milestone is M4.

### M4 sequence

~~~text
M4a — Persistent Personal Agent
      canonical conversation continuity

M4b — Memory
      explicit durable memory + provenance + retrieval

M4c — Projects
      full project/workspace model

M4d — Skills
      governed skill catalogue + enablement

M4e — Persistent Hermes Profiles
      richer native runtime/persona/profile continuity

M4f — Quantum Platform Guide
      ubiquitous researcher-facing agent UI

M4g — SSH Enterprise Client
      attach/resume/create conversations from terminal
~~~

M4a stays intentionally small. It proves that a personal conversation survives client and worker loss. It does not pull M4b-M4g forward.

See [M4 — Persistent Personal Agent](docs/M4-PERSISTENT-AGENTS.md).

## M4a acceptance principle

The defining test is destructive continuity:

~~~text
start project + conversation
        |
close browser
delete Jupyter Pod
disconnect SSH
restart personal agent worker
discard runtime-local session/cache
restart ACP API
        |
return from another client
        |
same project UUID
same conversation UUID
same transcript
same task/run history
same authorisation boundary
~~~

A second user must not be able to enumerate, retrieve or attach to that state.

The manual drill becomes a permanent automated conformance test.

## After M4

Once context is durable, the platform can safely become broader:

~~~text
Paperclip / Herdr / specialist agent runtimes
                    |
                    v
          A100 / H200 inference fabric
                    |
                    v
       model routing / evaluation / quotas
                    |
                    v
         Slurm accelerated execution
                    |
                    v
             QPU orchestration
~~~

Persistent context comes first so every later execution backend inherits the same identity, project and provenance model.

## Documentation

Start here:

1. [Documentation map](docs/README.md)
2. [Vision, objectives and principles](docs/01-vision-and-principles.md)
3. [Reference architecture](docs/02-reference-architecture.md)
4. [Repository boundaries](docs/03-repository-boundaries.md)
5. [Identity, tenancy and policy](docs/04-identity-tenancy-and-policy.md)
6. [Memory, state and storage](docs/05-memory-state-and-storage.md)
7. [Model and compute routing](docs/06-model-and-compute-routing.md)
8. [Runtimes, harnesses and sandboxes](docs/07-runtimes-harnesses-and-sandboxes.md)
9. [M4 persistent personal agent](docs/M4-PERSISTENT-AGENTS.md)
10. [Integration roadmap](docs/10-integration-roadmap.md)
11. [Threat model](docs/11-threat-model.md)

Implementation-specific documents such as the Phase-1 contract and ADE integration notes remain useful records, but they do not override the current architecture documents.

## Engineering and release discipline

Normal work branches from dev and returns through reviewed pull requests. Main remains the protected release boundary.

The platform follows a six-month major-release rhythm: roughly five months of development and staging integration followed by a release freeze/stabilisation month. Dependencies should remain close enough to upstream that ACP can adapt to evolving agent runtimes, model APIs, QRMI/QDMI and related interfaces without carrying an unnecessary long-lived fork.

## Public repository policy

This repository documents roles, interfaces, contracts and trust boundaries. It should not become the authoritative public map of live internal topology. Production addresses, credentials, private inventory and provider identifiers remain in protected environment data.

## License

Apache-2.0.
