# ADR-0005: Human approval for mutations

- Status: accepted
- Date: 2026-09-17

## Context

Infrastructure, security and research agents can propose high-impact changes. Prompt-level intent
and an agent's confidence are insufficient authority.

## Decision

Default all production capabilities to read/propose. A mutation requires an exact canonical plan
digest, authorised human approval, expiry, independent executor verification and audit. V0.1 keeps
direct production mutation capabilities disabled.

Telegram and Discord may notify but cannot approve high-risk operations.

## Consequences

Some workflows pause. This is intentional. Later low-risk runbooks may receive narrowly scoped
pre-authorisation through a separate ADR and evidence-based review.
