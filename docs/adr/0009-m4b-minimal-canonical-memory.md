# ADR 0009 — Minimal ACP-owned, explicitly approved research memory

**Status:** Proposed — review gate, not implementation authorization  
**Date:** 2026-10-30  
**Parent:** [M4b #31](https://github.com/nyameko/agent-control-plane/issues/31)  
**Depends on:** ADR 0007; M4a schema v3 and core continuity evidence in #21.

## Context and build-versus-adopt decision

M4a provides ACP-authoritative PostgreSQL conversations, messages, task/run history and an ephemeral Hermes adapter. A recovered transcript is **not** cross-conversation memory.

Substantial existing software overlaps our broader vision: LibreChat and Open WebUI offer polished multi-model chat; Letta offers self-hosted stateful agents/memory; LangMem provides reusable memory transformation primitives; Paperclip coordinates teams; GitHub Agentic Workflows automates repository work. We should benchmark rather than recreate these systems. ACP is justified **only as the thin, identity-bound, auditable interface** joining Quantum Platform's AgentPrincipal, governed research context, and eventually quantum-workflows scientific evidence across replaceable runtimes. It is not a general chatbot/agent framework competitor.

**Stop condition:** if an existing self-hosted memory implementation can meet the acceptance contract below at lower maintenance cost, using an ACP adapter, adopt it and cancel custom memory features. Even then, preserve ACP's signed identity/RLS and provenance contracts. Before expanding M4c–g, demonstrate value to researchers with an actual quantum-workflows execution.

## Decision: smallest vertical slice

1. **Canonical memory:** ACP PostgreSQL owns only approved-memory identity, immutable revisions and provenance; Hermes-native memory, embeddings and caches remain derived. No new database service.
2. **Scope:** private user only, bound to signed `tenant` and `urn:quantum-platform:user:<uuid>`. A project reference is contextual metadata, never a read grant. M4c introduces shared scope later.
3. **Source:** first MVP accepts exactly one existing, owner-visible, **user-authored canonical message** in ACP. Require source conversation ID, message ID and a SHA-256 of source content (integrity, not scientific verification).
4. **Promotion:** candidate -> approved/active requires an explicit, authenticated owner action. Never promote automatically or from imported history. No model-generated privileges.
5. **Revision semantics:** stable memory UUID, append-only revision sequence. Candidate, approved, corrected, revoked events. Correcting preserves UUID and historic audit. Revoking is terminal and prevents **future** retrieval (not erasure of backups/transcripts).
6. **Provenance and claims:** distinguish user-asserted preferences from verified scientific facts; do not claim a source is true because it was saved. A memory is source-linked, not an experimental result.
7. **Retrieval:** authenticated ACP query applies tenant/owner RLS and active/not-expired filters **before** ordering, returns bounded typed records with stable IDs/revisions/citations. Start deterministic newest-first with at most 8 items and 6k total characters. No vector DB/pgvector needed for the one-memory proof.
8. **Runtime:** extend `db.hydrate_personal_context` with `memories`; Hermes receives untrusted structured data with sources, not instructions or new tools. Keep `skip_memory=True`, temporary HERMES_HOME and no native memory promotion.
9. **Retention:** source FK prevents silent source deletion while memory is linked. Revocation is not legal erasure. Explicit purge/backup-retention policy remains separate and must be addressed before general availability.
10. **Migration/rollout:** v3-only `db.ready()` would fail after schema v4. Release and verify v3/v4-compatible API/worker first with memory disabled; then separately approve transactional v4 migration via manual parent GitOps app. App rollback must target compatible images, not old v3-only code.
11. **Safety:** forced PostgreSQL RLS on every table; app role without SUPERUSER/BYPASSRLS; append-only revisions and DB-enforced legal transitions; reviewable source digest; fail-closed unauthorized or stale retrieval; no stored provider secrets.

## Rejected for M4b MVP

- Separate vector store, graph, RAG indexing, historical chat imports, auto-extraction, shared memories, Paperclip integration or rewritten Hermes profiles.
- Replacing Quantum Platform identity with agent-framework identities or POSIX UIDs.
- Building a second chat product or expanding an agent-team task manager while quantum-workflows lacks a seamless research journey.

## Acceptance and product gate

**Technical:** researcher A explicitly approves one sourced memory in conversation C1; distinct C2 retrieves it using a fresh ephemeral Hermes runtime after browser/API/worker replacement; correction changes retrieval; revocation and expiry exclude it; B cannot list/read/approve/correct/revoke or retrieve A's memory; tests prove tenant/subject RLS and legacy M4a continuity. Record CI, schema checksum, run IDs, exact image digests and redacted observed evidence.

**User value:** do not treat SQL + recall as product completion. Pair M4b with a visible memory control and an actual quantum-workflows notebook/run/result journey. Pilot with researchers: task success, time-to-first-reproducible-result, run failure visibility, return usage and whether they choose the system voluntarily. These are evaluation criteria, not claimed results. Allocate the majority of new scientific engineering effort to quantum-workflows.

**Future option:** evaluate LibreChat/Open WebUI for UI and Letta/LangMem for memory/runtime reuse; preference for existing components does not waive the ACP authority/security contract.

## Consequences

Smaller M4b custom code, explicit consent, costly but auditable corrections, no silent cross-user leakage. M4b is a **bounded feature**, not a prerequisite to starting research notebooks. Re-evaluate ownership and implementation if the build-vs-buy test favors reuse.
