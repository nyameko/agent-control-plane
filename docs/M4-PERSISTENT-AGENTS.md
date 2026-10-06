# M4 — Persistent Personal Agents

M4 is the next product milestone after the M3 identity/workbench/execution vertical slice.

The purpose is not to add more agent frameworks. The purpose is to make one researcher's work **durable across surfaces and runtime restarts**.

## Acceptance criterion

Start a project/conversation in Quantum Platform, then:

1. close the browser;
2. delete/recreate the user's Jupyter Pod;
3. disconnect SSH;
4. restart the Hermes/ACP worker;
5. reconnect from another supported client.

The same project, conversation history, approved memories, skills and task/run history must still be available.

If this fails, M4 is not complete.

## Canonical ownership

```text
Quantum Platform
  human identity, programmes, entitlements
          │
          ▼
Agent Control Plane
  canonical conversations
  projects
  memories
  skills
  task/run/audit history
          │
          ▼
runtime adapters
  Hermes first
  Paperclip/meta-harness later
  coding/runtime adapters later
```

Runtime-local state is useful but non-canonical.

## M4a — Conversation persistence

Deliver:

- Conversation model;
- Message model;
- project/context binding;
- resumable event stream;
- user/tenant authorization;
- archive/export/delete semantics;
- runtime-session correlation.

Portal, Jupyter and SSH/TUI clients must reference the same conversation UUID rather than maintain separate histories.

## M4b — Project model

A Project is a first-class research/engineering context.

Example:

```text
Project
├── owner/members
├── repositories
├── workspace/artifact references
├── conversations
├── tasks/runs
├── memories
├── skills
└── execution history
```

Projects should be usable for software engineering, HPL optimisation, Hamiltonian simulation, literature/research work and teaching cohorts.

## M4c — Memory

Keep memory classes distinct:

- working context;
- episodic task/run summaries;
- semantic durable facts with provenance;
- procedural skills/playbooks;
- explicit user preferences.

Conversation history is not automatically permanent memory.

Promotion:

```text
conversation/tool/run evidence
        ↓
candidate memory
        ↓
policy + provenance + optional confirmation
        ↓
versioned durable memory
```

## M4d — Skills

Skills are reviewed procedural capabilities, not arbitrary hidden prompt text.

Shared skills should be versioned in Git when practical.

Private/user-specific skill adaptations need explicit scope and ownership.

## M4e — Persistent Hermes profile

Hermes is the first runtime adapter.

Early M4 may use one isolated persistent Hermes profile per user/project or a small mapped set of profiles.

The Agent Control Plane must retain:

- canonical user/project identity;
- conversation/task/run identifiers;
- runtime session/profile mapping;
- runtime version;
- model routing evidence.

Hermes SQLite/profile data must not become the canonical multi-user platform database.

## M4f — Quantum Platform Guide

Quantum Platform should expose a persistent Guide/co-scientist panel backed by ACP.

The Guide can:

- explain platform use;
- guide environment setup;
- help choose execution offerings;
- inspect user's authorized run history;
- help interpret workflow manifests;
- continue project discussions across sessions.

It should not gain broad infrastructure administrator credentials.

## M4g — SSH / Enterprise client

The future SSH experience is a user-space client of the same ACP APIs.

Conceptually:

```text
╭──────────── QUANTUM PLATFORM ─────────────╮
│ Project      HPL optimisation             │
│ Workbench    running                      │
│ Runs         2 active                     │
│ Agent        connected                    │
│                                           │
│ [A] Agent [P] Projects [R] Runs [S] Shell│
╰───────────────────────────────────────────╯
```

The client may integrate with Herdr for terminal/agent supervision, but Herdr is not the source of platform identity, conversation history or authorization.

The normal shell must remain available.

## Paperclip/meta-harness boundary

Paperclip may later coordinate multiple runtime/harness adapters:

```text
ACP
 │
Paperclip
 ├── Hermes
 ├── Codex adapter
 ├── Claude Code adapter
 └── local/open-source adapters
```

Do not make Paperclip the canonical database.

## M4 data durability

Minimum durable stores:

- PostgreSQL for canonical control state;
- persistent runtime profile storage where needed;
- NFS/parallel/project storage for user workspaces;
- object/artifact storage as the platform grows;
- Git for reviewed definitions/skills/policies.

## M4 security boundary

Persistent context increases sensitivity.

M4 must enforce:

- user/project authorization on every conversation/memory retrieval;
- explicit memory provenance;
- deletion/export controls;
- secret exclusion/redaction;
- no cross-user retrieval by default;
- audit trail for privileged access;
- short-lived delegated credentials for execution/tool calls.

## M4 → later milestones

After M4 provides durable project/agent state:

```text
M5 accelerated execution providers
  A100 / H200 / remote providers
        ↓
M6 HPL/MPI/GPU benchmark journey
        ↓
M7 quantum simulation environments
        ↓
M8 QPU/provider journey
        ↓
advanced QCSC/HEP/Hamiltonian workflows
```

Building persistent agents first means the later benchmark/research workflows automatically inherit experiment continuity and cross-surface assistance.
