# M4b-1 — Minimal memory schema and authenticated API contract

**Status:** Proposed, review gate. No deployed endpoint or schema change.  
**Parent:** [ACP #31](https://github.com/nyameko/agent-control-plane/issues/31).  
**Architecture:** [ADR 0009](adr/0009-m4b-minimal-canonical-memory.md).

## 1. Canonical v4 data model

Two tables only:

`acp1.memory_item`: `id uuid`, `tenant text`, `owner_subject text`, `creation_key uuid`, `creation_payload_sha256 char(64)`, `scope_kind='private_user'`, `kind in (preference,episodic,semantic,project_note)`, `status in (candidate,active,revoked)`, `current_revision int`, `source_conversation_id uuid`, `source_message_id uuid`, `source_sha256 char(64)`, `sensitivity in (internal,confidential)`, `verification_status in (user_asserted,source_supported,unverified)`, optional `confidence`, `created_at`, `updated_at`, `approved_at`, `expires_at`, `revoked_at`. Unique `(tenant,owner_subject,id)` and `(tenant,owner_subject,creation_key)`; FK to source `(tenant,owner_subject,conversation_id,message_id)`.

`acp1.memory_revision`: immutable `(memory_id,revision)`; same `tenant,owner_subject`, `event_type in (candidate_created,approved,corrected,revoked)`, `body text` (null for revoked), `actor_subject`, `reason`, `created_at`. Each memory item's `(id,current_revision)` must point to its own revision using a deferred FK. Creation and transition must be atomic; explicit legal transition and append-only guards are required **in PostgreSQL**, not only in API handlers.

Revision behavior:

| Operation | Before | After | Event | Body |
|---|---|---|---|---|
| create | none | candidate, rev 1 | candidate_created | proposed content |
| approve | candidate, rev N | active, rev N+1 | approved | reviewed content |
| correct | active, rev N | active, rev N+1 | corrected | replacement |
| revoke | candidate/active, rev N | revoked, rev N+1 | revoked | null |
| expire | active, expires_at <= now | remains active, excluded by SELECT | no synthetic event | unchanged |

The original message must be user-authored and in an active conversation; check this in the API transaction, with composite source FK providing ownership and reference integrity. Source SHA is over canonicalized serialized content and is *not* epistemic truth. A superseding new memory, project sharing, derived indexes, run-source links, imported archives and purge APIs are deferred.

## 2. Signed principal and authorization

Existing Quantum Platform server issues short-lived EdDSA `agent:personal` assertion. ACP determines subject/tenant from claims, never from body/query parameters. Existing `db.scoped` sets transaction-local `acp.tenant_id` and `acp.subject_id`. Apply `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY` on both tables, grant only needed privileges to `acp_app`. No inherited administrator read grants.

No endpoint returns memory belonging to another subject, even if an ID is guessed. Foreign IDs -> `404`. Missing/invalid assertion -> `401`; valid but insufficient scope -> `403` (update existing `require_personal` behavior separately if necessary). Bad body -> `422`; stale revision/idempotency-key-with-different-payload -> `409`; unavailable database -> `503`. Never turn cross-user misses into `403` that reveals existence.

## 3. Proposed API (not yet implemented)

```text
POST /v1/memories/candidates                 Idempotency-Key: <uuid>
  {source_conversation_id,source_message_id,kind,body,
   sensitivity:"internal",expires_at?:ISO8601}
  -> 201 {id,status:"candidate",revision:1,provenance...}
  replay identical -> 200 same id; changed payload -> 409

POST /v1/memories/{id}/approve              If-Match: "<revision>"
  {body?:approved_text} -> 200 {id,status:"active",revision:N+1}
  candidate only

GET /v1/memories?status=active|candidate|revoked
  -> 200 {items:[...],limit:100}
GET /v1/memories/{id}
  -> 200 current revision plus source IDs and revision metadata

PATCH /v1/memories/{id}                     If-Match: "<revision>"
  {body:corrected_text,reason?:text} -> 200 {revision:N+1}
  active only

POST /v1/memories/{id}/revoke               If-Match: "<revision>"
  {reason?:text} -> 200 {status:"revoked",revision:N+1}
  candidate or active; terminal

GET /v1/memories/retrieve?limit=8
  -> 200 {items:[{id,revision,kind,body,source_conversation_id,
     source_message_id,verification_status,expires_at}], ...}
```

Request constraints: body 1..2000 chars; source is one exact user message; no raw credentials, provider keys or user-supplied owner. Admission filters are defense in depth, not a guarantee to detect every secret. First version private-owner only. Authenticated browser proxy retains upstream statuses 409/422 rather than collapsing them into 503.

**Ordering caveat:** static `/v1/memories/retrieve` must be declared before dynamic `/v1/memories/{id}` (or use a distinct route) to prevent incorrect route matching.

## 4. Retrieval and Hermes execution

1. Verify signed principal and authorized tenant.
2. Begin SQL transaction with owner-scoped RLS.
3. SELECT only `scope_kind='private_user'`, `status='active'`, `approved_at IS NOT NULL`, `expires_at IS NULL OR expires_at > now()`.
4. Join only current immutable revision; exclude revoked body; limit 8, at most 2000 chars/item and 6000 chars aggregate.
5. Return IDs, revision and provenance; inject into separate `memories` field of context reconstructed for a new conversation.
6. Treat memory text as **untrusted research data**, never as policy, system prompts, tool grants or proof of a scientific finding.
7. If no memory: preserve transcript-only M4a behavior. If DB/RLS check fails: fail closed; never substitute other user's context.

No pgvector, model-driven extraction or runtime SQLite persistence in first vertical slice.

## 5. Verification and sequencing

- **PR 1 (this review gate):** ADR and this contract only.
- **PR 2:** app binaries compatible with schema 3 or 4, feature disabled; CI tests readiness matrix (2 rejects; 3 and 4 pass; 5 rejects) and legacy behavior.
- **PR 3:** forward-only packaged `0004` migration + checksum and migration/RLS/immutability/transition tests, no execution in cluster. Do not merge until PR 2 reviewed and deployed on v3.
- **Then:** API lifecycle PR, retrieval/Hermes PR, minimal UI PR, controlled GitOps, manual and automated destructive conformance. M4b issue #31 closes only after observed end-to-end proof.

## 6. Non-goals and delivery priority

Paperclip team orchestration, advanced M4c projects, M4d skills, M4e Hermes profiles, M4f Guide, M4g SSH, chat imports and knowledge graphs are not M4b prerequisites. The **quantum-workflows** first-user scientific notebook/run/result journey must continue in parallel. Prefer buying/reusing frontend, memory and team features where existing tools meet the explicit contract.
