# ADR 0007 — ACP owns canonical agent context

Status: accepted.

## Context

Portal, Jupyter, editors, terminal clients and agent runtimes can all maintain native session state. If any one of them becomes the only authoritative copy, replacing that component risks data loss or competing histories.

M4 requires conversation continuity across client and runtime loss.

## Decision

Agent Control Plane owns the canonical portable agent context:

- projects;
- conversations/messages;
- memory;
- skill bindings;
- task/run history;
- runtime/session mappings;
- routing/approval metadata.

Runtime-local state is secondary.

Quantum Platform remains human-identity authority, quantum-workflows remains scientific-provenance authority, and schedulers/providers remain execution-state authorities.

## Consequences

Runtime frameworks can be replaced behind adapters without migrating user history.

ACP PostgreSQL becomes a critical durable service and must have backup/restore/conformance testing.
