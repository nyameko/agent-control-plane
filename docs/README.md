# Agent Control Plane documentation

This documentation is organised by **authority**, not by the date a document happened to be written.

The architecture documents below define the current design. Implementation contracts and integration reviews explain specific slices or experiments. If an older implementation note conflicts with an authoritative architecture document, the architecture document wins unless a newer ADR explicitly changes the decision.

## Authoritative architecture

| Document | Question it answers |
| --- | --- |
| [01 — Vision, objectives and principles](01-vision-and-principles.md) | Why does ACP exist and what principles are non-negotiable? |
| [02 — Reference architecture](02-reference-architecture.md) | What are the layers, contracts, state flows and failure boundaries? |
| [03 — Repository boundaries](03-repository-boundaries.md) | Which repository/system owns each concern? |
| [04 — Identity, tenancy and policy](04-identity-tenancy-and-policy.md) | How are users, AgentPrincipal UUIDs, POSIX identities, tenants and capabilities related? |
| [05 — Memory, state and storage](05-memory-state-and-storage.md) | Which state is canonical, derived, runtime-local or externally authoritative? |
| [06 — Model and compute routing](06-model-and-compute-routing.md) | How can models and execution targets change without changing user context? |
| [07 — Runtimes, harnesses and sandboxes](07-runtimes-harnesses-and-sandboxes.md) | How do Hermes, Paperclip and alternative runtimes fit without becoming platform authorities? |
| [08 — Clients and messaging](08-clients-chat-telegram-discord.md) | How do web, Jupyter, editor, terminal and messaging clients attach to the same context? |
| [09 — Observability, evaluation and provenance](09-observability-evaluation-and-provenance.md) | How do we measure, audit and reproduce what agents did? |
| [10 — Integration roadmap](10-integration-roadmap.md) | In what order should the architecture become real? |
| [11 — Threat model](11-threat-model.md) | What are the primary security threats and controls? |

## Current milestone

The current product milestone is **M4 — durable personal agents**.

- [M4 — Persistent Personal Agent](M4-PERSISTENT-AGENTS.md)
- [Quick Start for contributors](QUICK_START.md)

The fixed M4 order is:

~~~text
M4a  Persistent Personal Agent
M4b  Memory
M4c  Projects
M4d  Skills
M4e  Persistent Hermes Profiles
M4f  Quantum Platform Guide
M4g  SSH Enterprise Client
~~~

M4a must remain narrow. It establishes canonical conversation continuity and failure recovery. Memory, rich project workspaces, skills and runtime-persona persistence are later sub-milestones.

## Implementation contracts and integration notes

These documents are important evidence of how a particular slice was designed or implemented. They are intentionally more concrete and may age faster than the architecture documents.

| Document | Role |
| --- | --- |
| [12 — Phase 1 implementation contract](12-phase1.md) | Executable v0.2 administrative diagnostic slice |
| [13 — ADE workflow](13-ade-workflow.md) | Spacemacs/gptel, Hermes, Herdr, Herder and Glyph integration analysis |
| [14 — Integration status and trajectory](14-integration-review.md) | Reconciles current repository state with the target architecture |
| [Repository review](REPOSITORY-REVIEW.md) | Earlier source/repository findings that informed the design |
| [References](REFERENCES.md) | Upstream projects, standards and research references |

## Architectural decision records

ADRs are the stable decisions beneath the wider prose:

- [ADR-0001 — use Agent Control Plane](adr/0001-use-agent-control-plane.md)
- [ADR-0002 — ACP is not a resource scheduler](adr/0002-control-plane-is-not-resource-scheduler.md)
- [ADR-0003 — state has explicit owners](adr/0003-state-has-explicit-owners.md)
- [ADR-0004 — Hermes first, pluggable harnesses](adr/0004-hermes-first-runtime-pluggable-harnesses.md)
- [ADR-0005 — human approval for mutations](adr/0005-human-approval-for-mutations.md)
- [ADR-0006 — research workbench is a client](adr/0006-research-workbench-client.md)
- [ADR-0007 — ACP owns canonical agent context](adr/0007-acp-canonical-agent-context.md)
- [ADR-0008 — AgentPrincipal UUID is the durable user subject](adr/0008-agentprincipal-not-posix-identity.md)

## Documentation rule

Every new subsystem must answer four questions before code is accepted:

1. Who owns its canonical state?
2. Which identity and tenancy boundary authorises access?
3. Which portable contract separates it from ACP?
4. What failure/restart test proves the boundary is real?

If those answers are unclear, the integration is not ready.
