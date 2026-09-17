# ADR-0004: Hermes first, pluggable harnesses

- Status: accepted
- Date: 2026-09-17

## Context

Hermes provides the broadest immediate match for persistent profiles, skills, memory, tools,
subagents, approvals, messaging and programmatic APIs. Other harnesses will evolve.

## Decision

Implement Hermes as the first full runtime adapter. Keep task, event, approval and artifact
contracts independent of Hermes. Add other runtimes only through conformance-tested adapters.

## Consequences

Hermes can be used deeply without becoming platform identity, global policy or canonical storage.
Experimental harnesses do not destabilise client and database contracts.
