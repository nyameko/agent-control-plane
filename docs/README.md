# Documentation map

Read the documents in order for the full design. Architectural decisions in `adr/` are short,
stable records; the numbered guides explain the wider rationale and implementation path.

| Document | Purpose |
| --- | --- |
| [Repository review](REPOSITORY-REVIEW.md) | source snapshots and findings that shaped this commit |
| [01 — Vision and principles](01-vision-and-principles.md) | the virtual organisation model and its non-negotiable rules |
| [02 — Reference architecture](02-reference-architecture.md) | components, trust boundaries and request flow |
| [03 — Repository boundaries](03-repository-boundaries.md) | exact ownership across existing projects |
| [04 — Identity, tenancy and policy](04-identity-tenancy-and-policy.md) | users, programmes, service principals, capabilities and approvals |
| [05 — Memory, state and storage](05-memory-state-and-storage.md) | PostgreSQL, Cinder, object storage, Git, vector data and secrets |
| [06 — Model and compute routing](06-model-and-compute-routing.md) | two independent placement decisions and resource policy |
| [07 — Runtimes, harnesses and sandboxes](07-runtimes-harnesses-and-sandboxes.md) | Hermes, other harnesses and isolated execution |
| [08 — Clients and messaging](08-clients-chat-telegram-discord.md) | persistent web/Jupyter/gptel chat plus Telegram/Discord liaison |
| [09 — Observability and evaluation](09-observability-evaluation-and-provenance.md) | telemetry, audit, quality, cost and scientific provenance |
| [10 — Integration roadmap](10-integration-roadmap.md) | phased changes in all four repositories |
| [11 — Threat model](11-threat-model.md) | concrete attack surfaces and mitigations |
| [References](REFERENCES.md) | upstream projects and protocols reviewed for this design |

## Decision records

- [ADR-0001: use `agent-control-plane`](adr/0001-use-agent-control-plane.md)
- [ADR-0002: the control plane is not a resource scheduler](adr/0002-control-plane-is-not-resource-scheduler.md)
- [ADR-0003: state has explicit owners](adr/0003-state-has-explicit-owners.md)
- [ADR-0004: Hermes first, pluggable harnesses](adr/0004-hermes-first-runtime-pluggable-harnesses.md)
- [ADR-0005: human approval for mutations](adr/0005-human-approval-for-mutations.md)

## Executable Phase 1 and ADE integration

- [Phase 1 implementation contract](12-phase1.md)
- [Spacemacs, Hermes, Herdr, Herder and Glyph](13-ade-workflow.md)
- [Integration review and future roadmap](14-integration-review.md)
