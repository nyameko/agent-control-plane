# Agent Control Plane wiki

**Agent Control Plane (ACP)** supplies a durable, self-hostable research context across the Quantum Platform browser, notebooks, terminal and future editor clients. It coordinates authorised agents, models and task/run history without becoming a superuser, a scheduler or a second scientific workflow engine.

**Source snapshot:** 4 November 2026, default branch `main`. M4c/M4e schema and interface implementations in source may be ahead of the **live** PostgreSQL schema or deployed image. Health endpoints are not proof of feature conformance.

## Navigation

| Goal | Article |
|---|---|
| Understand the architecture and source of truth | [Architecture](Architecture.md) |
| Use projects, conversations and memory | [Researcher guide](Researcher-guide.md) |
| Integrate Quantum Guide/Jupyter/terminal | [Clients and integrations](Clients-and-integrations.md) |
| Configure open-weight models and harnesses | [Models and runtimes](Models-and-runtimes.md) |
| Run ACP, inspect schemas, promote releases | [Operator runbook](Operator-runbook.md) |
| Build APIs, migrations, tests and workers | [Developer guide](Developer-guide.md) |
| Follow endpoint and authorization contracts | [API and data contracts](API-and-data-contracts.md) |
| Diagnose continuity and permission failures | [Troubleshooting](Troubleshooting.md) |
| Apply security, isolation and approval rules | [Security and tenancy](Security-and-tenancy.md) |
| Request features or fix docs | [Contributing](Contributing.md) |

Start with [README](https://github.com/nyameko/agent-control-plane/blob/main/README.md), [reference architecture](https://github.com/nyameko/agent-control-plane/blob/main/docs/02-reference-architecture.md), [M4 specification](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4-PERSISTENT-AGENTS.md) and [live release gates](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md).

## Guide discovery and support

[Guide integration, issue routing and safe agent retrieval](Guide-assistance.md) · [machine-readable page index](guide-index.json). Neither documentation nor its index grants resource permissions.


## Detailed engineering and reliability references

- [Database RLS and migrations](Database-RLS-and-migrations.md)
- [Memory lifecycle and provenance](Memory-lifecycle-and-provenance.md)
- [Harness lifecycle and continuity](Harness-lifecycle-and-continuity.md)
- [ACP release and conformance](ACP-release-and-conformance.md)
- [Agent security checklists](Agent-security-checklists.md)
