# ADR-0003: State has explicit owners

- Status: accepted
- Date: 2026-09-17

## Context

Hermes state, portal user data, conversation history, workspaces, scientific artifacts, metrics and
secrets have different consistency and retention needs.

## Decision

Use PostgreSQL for canonical control records, Cinder PVCs for mutable runtime/workspace files,
object storage for large immutable artifacts, Git for reviewed declarations, a secret broker for
credentials, and telemetry systems for operational observations.

## Consequences

Every new data type must declare its canonical owner, retention, sensitivity, backup and deletion
behaviour. Runtime PVC loss cannot erase canonical task/audit history.
