# M4c — minimal project and programme API contract (review draft)

**Status:** Contract only; no new endpoint, schema v5 migration, JWT scope or entitlement adapter is implemented by this document.

This contract is the implementation gate for [ACP #48](https://github.com/nyameko/agent-control-plane/issues/48) and [M4 release #45](https://github.com/nyameko/agent-control-plane/issues/45). All routes are ACP server-side routes; Quantum Platform proxies authenticated requests. UUIDs below are illustrative type placeholders.

## Existing routes to preserve

- `POST /v1/projects`, `GET /v1/projects`: currently private owner-scoped `id,title,created_at,updated_at,archived_at`.
- `POST /v1/conversations`, `GET /v1/conversations[?project_id=]`, `GET /v1/conversations/{id}`, `POST /v1/conversations/{id}/turns`, `GET /v1/runs/{id}`.
- `/v1/memories/*`: stay private, source-bound and governed by M4b. Personal endpoints use signed `agent:personal`.

No alternate conversation or memory database may be introduced by the browser, runtime or a programme folder.

## Slice C1 — private workspace usability, no shared authorization

Proposed additions after HTTP/retention review:

| Route | Request | Contract |
| --- | --- | --- |
| `GET /v1/projects/{id}` | — | Owner-only metadata and typed references, 404 for invisible |
| `PATCH /v1/projects/{id}` | `{title?, archived?}` | Rename or archive; optimistic `If-Match`; no physical deletion |
| `PATCH /v1/conversations/{id}` | `{title?, project_id?, archived?, pinned?}` | Owner-only rename/move/unfile/archive/pin; no cross-owner project |
| `GET /v1/conversations?cursor=&limit=&project_id=` | cursor + bounded limit | Stable ordering and paging, not merely most recent 100 |

All patch fields optional but require at least one mutation; `title` 1–200 chars, `project_id: null` unfiles, stable `id`, version increments on mutations. No "delete" UI unless lifecycle, retention, memory-source references and export are explicitly specified. Archive of project does **not** destroy or transfer its conversations; agree visibility and move behaviour before activation. Return 404 for nonexistent **or forbidden** identifiers; conflict/version error 409 or 412; invalid input 422. Existing M4a clients must continue working unchanged.

Repository/artifact/run references are typed metadata only: `{kind,provider,immutable_ref,commit_or_digest?,created_at}`, not arbitrary URLs used as tool permissions. Do not copy scientific results into ACP; link to Quantum Platform ExecutionRecord and quantum-workflows manifest with independently validated IDs.

## Slice C2 — PI-owned programme conversations (schema v5 review required)

New distinct entities, proposed minimum:

- `programme_space(id, tenant, platform_programme_id, status, created_by_subject, created_at, updated_at)`, with unique platform identity per tenant. No ACP membership ledger as authority.
- `programme_conversation(id, tenant, space_id, title, created_by_subject, state, created_at, updated_at, version)`.
- `programme_message(id, tenant, conversation_id, seq, author_subject, author_kind, content, source_channel, client_message_id, run_id?, created_at)`; unique sequence and retry protection.
- `programme_audit_event(id, tenant, actor_subject, target_id, action, decision, occurred_at, metadata)`, redacted.
- Optional association table for typed references *only after* proving one real workflow/result use case.

Every programme table uses `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`. Application DB role must not have `BYPASSRLS`. SQL policies must ensure isolation independently of API validation; prefer explicit, transaction-scoped verified programme grants, fail closed when absent. Scope/session variables cannot be accepted from an HTTP client. Never attach programme reads to private `owner_subject` policies.

Proposed routes:

| Route | Authorization | Result |
| --- | --- | --- |
| `GET /v1/programme-spaces` | Verified approved active membership | Spaces actually visible to principal |
| `POST /v1/programme-spaces` | PI/delegate, exact programme | Canonical UUID, platform programme key |
| `GET /v1/programme-spaces/{id}/conversations` | Active member | Bounded list with cursor |
| `POST /v1/programme-spaces/{id}/conversations` | PI/delegate for first release | Create room; idempotency key |
| `GET /v1/programme-conversations/{id}` | Active member, revalidated | Ordered transcript + authors |
| `POST /v1/programme-conversations/{id}/messages` | Active member, revalidated | User message only, bounded payload, idempotent retry |
| `PATCH /v1/programme-conversations/{id}` | PI/delegate | Title/archive, version precondition |

Shared agent execution is a **subsequent reviewed PR** with per-user and programme quotas, model cost attribution, explicit tool allowlist and approved capability grants. It must not inherit `agent:personal`. Do not enable an agent post endpoint in C2.

## Entitlement contract / revocation decisions requiring sign-off

Quantum Platform must expose a narrow **trusted service-to-service** membership decision (or equivalently secure signed short-lived grant with online revocation):

- Request: authenticated principal UUID, immutable programme ID, requested action, request ID.
- Response: `allow`, trusted programme UUID/ID, decision time, bounded expiry, membership version / revocation epoch, effective role, audit correlation ID.
- Decision: `active && approved && programme_active && action_allowed`; on timeout/error => deny, not fallback to stale allow.
- New ACP scopes: narrowly separated `agent:programme:read`, `agent:programme:write`, `agent:programme:manage` (proposal, not active).
- Cache: **no positive authorization caching for initial release** unless a verified invalidation mechanism guarantees revocation before next access; no browser-controlled membership claims.

Resolve before schema PR: revocation propagation latency; changing PI; archived programme; which active members see content after the author leaves; deletion/retention/export; tenant mapping; whether different platform institutions share a tenant; maximum shared message size; signed-grant replay and failure semantics.

## PR sequence and acceptance matrix

1. **ACP C1**: private project/conversation lifecycle API + DB integration tests; QP matching signed proxies + Quantum Guide real menus; no UI-only state.
2. **Platform entitlement**: documented, audited member/PI service authorization, active/revoked tests, no new admin privileges.
3. **ACP C2 schema**: forward-only v5 migration + compatibility-first API/worker + FORCE RLS + source-of-truth checks. Never run migrator during a routine parent Argo sync.
4. **ACP C2 APIs**: list/create/read/post, pagination, concurrency and author attribution; no group model call.
5. **QP C2 UI**: authorized programme folder -> canonical room transcript with truthful empty/denied/error states.
6. **Optional later**: group agent invocation, explicit private-to-shared copy, scoped approved resources; independently reviewed.

Test matrix includes: same tenant different user; distinct tenant; unrelated programme; PI vs member vs delegate; suspended/revoked user; stale grant; unavailable entitlement source; rapid revocation during turn; duplicate submission; concurrent posts; forgotten project UUID; private-memory isolation; browser/Jupyter/SSH canonical resume. Assert both HTTP and SQL/RLS failures. Capture committed SHAs, checksum, image digests, CI, operator evidence and human approval; no acceptance claim from documentation alone.

**No-regression gate:** M4a destructive continuity, M4b private-memory correction/revoke, and the existing Quantum Guide approval interface all remain functional.
