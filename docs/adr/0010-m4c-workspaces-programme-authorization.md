# ADR 0010 — Separate private ACP projects from PI-governed programme spaces

**Status:** Proposed — architecture and authorization review gate, no migration or production rollout
**Date:** 2026-10-31
**Parent:** [M4c #48](https://github.com/nyameko/agent-control-plane/issues/48), [integrated M4 #45](https://github.com/nyameko/agent-control-plane/issues/45)
**Depends on:** ADR 0007–0009; existing M4a personal project/conversation tables, M4b private memories, Quantum Platform programme memberships.

## Context

M4a already provides owner-scoped `acp1.project`, `acp1.conversation`, `acp1.message`, and task/run tables. M4b's memory table explicitly permits only `private_user`. Quantum Platform owns ResearchProgramme and ProgrammeMembership with approved statuses and PI roles. Quantum Guide currently displays approved programme *folders*; those folders cannot confer access to shared chat. Neither ACP's personal project foreign key nor a caller-supplied programme ID is sufficient authorization.

The goal is useful, portable research workspaces without creating another project-management application or bypassing platform permissions.

## Decision

1. **Preserve private objects unchanged.** An ACP private project remains owned by exactly one stable AgentPrincipal subject inside a tenant. Its existing owner-subject/tenant forced RLS is neither broadened nor replaced by membership checks. Private memories stay private; no implicit inheritance to project/programme.
2. **Separate shared entities.** Add a distinct ACP `programme_space` and `programme_conversation`/message history with its own authorization path. Bind `programme_space` to an immutable Quantum Platform ResearchProgramme identifier (do not use a mutable slug). Do not set `owner_subject` to a group ID or reparent personal conversations.
3. **Platform is the programme membership oracle.** PI, delegated manager, active approved member, and denied/revoked are resolved by trusted Quantum Platform server-side authorization. Never trust the browser's role, programme folder, or unverified JWT custom attributes. Define short-lived signed, audience-bound, replay-resistant grants plus an immediate revocation/freshness mechanism **before** shared history is readable. A static long-lived membership snapshot is insufficient.
4. **ACP is the conversation and audit authority.** ACP stores stable shared room UUID, author AgentPrincipal subject, per-message sequencing and provenance, action/audit events, and typed references to Git repositories, workspaces, workflow manifests and results. Platform owns scientific ExecutionRecord and entitlement; the scheduler owns resource allocation.
5. **Distinct scopes and privilege checks.** Personal `agent:personal` grants no programme-chat access. New named scopes for programme read/write/manage are checked by ACP and are backed by verified membership. No admin/diagnostic or GPU/QPU/tool permission is gained by joining a room.
6. **Default-deny lifecycle.** Only the PI/approved delegate can create/manage rooms; approved active members may read/post. Former members lose history access immediately on next authorization check. PI handoff, suspended programme, export, retention and deletion must have explicit states. Existing group history remains owned by the programme, subject to policy, not retroactively claimed as a former user's private history.
7. **No silent sharing.** A private conversation remains private until an explicit, warned, audited **copy** into a shared conversation is approved. A copied message has source attribution and privacy review; no personal memory, provider secret, file or tool trace is copied by default. For the initial slice, disable private-to-shared copy entirely.
8. **Safe sequencing.** First ship owner-scoped project/conversation rename, move, pin/archive endpoints using existing v4-compatible schema where possible. Then review a forward-only v5 programme schema/contract, run RLS and membership tests, add UI and only later opt in group agent turns. The first shared-message PR must not execute agents.
9. **Build versus adopt.** Reuse existing Quantum Guide navigation, GitHub issue/PR tracking, Jupyter, Slurm and quantum-workflows manifests. Do not build Paperclip, a document store, collaborative whiteboard or another scheduling/accounting layer within ACP.

## Alternatives rejected

- Changing the private project RLS predicate to `owner OR member` for a mixed table: high risk of cross-scope leaks and M4b regression.
- Trusting client programme ID or stale role claims for reads: allows membership revocation windows.
- Duplicating Platform ResearchProgramme and membership state in ACP: creates divergent authority.
- Building a general project-board service: distracts from reproducible quantum-workflows.

## Required proof before feature activation

- Cross-tenant, owner A/B, programme X/Y, PI, approved member, unauthorized member, revoked member; SQL RLS **and** HTTP checks for every CRUD/read/turn path.
- User A's private project, transcript and memory never appear in shared APIs, prompts or search, even if A belongs to the same programme.
- Membership revocation takes effect before subsequent read, post or model hydration; authoritative source unavailable => deny.
- Concurrent posts have stable ordering; duplicate client retry does not create duplicate turns; group messages carry author/channel/run identifiers.
- Full-browser / Jupyter / SSH continuity reuses canonical UUIDs; actual destructive runtime restart adds no alternate state.
- Audit redacted, with actual programme, subject, decision reason and revocation evidence; no tokens or raw private memory in logs.
- Two-researcher acceptance, after an independently reviewed rollout; no deployment or migration is authorized by this ADR.

## Scope discipline

M4c ends once a PI can create a programme conversation, two approved members collaborate, and a revoked member is denied everywhere, while individual private data remains isolated. Advanced team management, shared memory, social channel mirrors and rich multi-agent delegation belong to later reviewed work, not this gate.
