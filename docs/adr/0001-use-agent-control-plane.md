# ADR-0001: Use `agent-control-plane`

- Status: accepted
- Date: 2026-09-17

## Context

The new repository coordinates agents across infrastructure, user platform, scientific workflows
and future projects. `agent-platform` would be ambiguous beside `quantum-platform` and could imply
ownership of the full user-facing platform.

## Decision

Name the repository `agent-control-plane`.

## Consequences

The repository owns cross-cutting decisions, policy, delegation and state contracts. It does not
own every UI, model server, compute scheduler or production manifest.
