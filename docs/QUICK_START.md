# Quick Start

## What this service is

Agent Control Plane (ACP) is the durable policy and orchestration layer between authenticated platform users and pluggable agent runtimes.

It is **not**:

- the Kubernetes scheduler;
- the Slurm scheduler;
- the model inference server;
- the canonical user database;
- a privileged shell bot.

## Current direction

The immediate milestone is [M4 Persistent Personal Agents](M4-PERSISTENT-AGENTS.md).

The required user experience is:

```text
Quantum Platform ─┐
Jupyter ──────────┼──► ACP ───► Hermes/runtime
SSH/TUI ──────────┤
gptel ────────────┘
```

All clients bind to the same canonical project/conversation state.

## Local development

Use the repository's existing Python/application setup and run the current test suite before changing runtime adapters or schemas.

Start with the documentation:

1. [Vision and principles](01-vision-and-principles.md)
2. [Reference architecture](02-reference-architecture.md)
3. [Repository boundaries](03-repository-boundaries.md)
4. [Memory/state/storage](05-memory-state-and-storage.md)
5. [Runtimes/harnesses](07-runtimes-harnesses-and-sandboxes.md)
6. [M4 persistent agents](M4-PERSISTENT-AGENTS.md)
7. [Integration roadmap](10-integration-roadmap.md)

## State rule

When adding a new integration, write down **who owns the canonical state**.

Example:

```text
conversation history      → ACP/PostgreSQL
Hermes session mapping    → ACP + runtime adapter
Hermes local cache        → Hermes profile
research files            → user/project storage
workflow result           → quantum-workflows artifact/provenance
scheduler state           → Slurm/provider, referenced by ACP/platform
```

Do not create a second hidden canonical database because a runtime happens to ship one.

## First M4 vertical slice

The smallest useful implementation is:

```text
authenticated user
  ↓
create project
  ↓
create conversation
  ↓
send message
  ↓
Hermes adapter
  ↓
persist response/events
  ↓
restart worker
  ↓
resume same conversation
```

Only after that works should memory promotion, more harnesses or autonomous agents expand.
