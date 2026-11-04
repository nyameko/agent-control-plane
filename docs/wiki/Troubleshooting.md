# Troubleshooting ACP

## /ready is healthy but Guide is missing a feature

Check deployed image digests, Argo resource drift, database `schema_version` and corresponding required tables. Readiness may deliberately tolerate older schemas. Do not conclude that memory, rooms, profiles or terminal pairing passed live acceptance.

## Conversation vanished after restart

Confirm the same authenticated AgentPrincipal UUID, project/conversation UUID, API route and canonical PostgreSQL data. Compare client state to stored messages; test after worker/browser restart only in an approved test tenant. If only a runtime cache retains a response, continuity is broken.

## Wrong user sees a record

Treat as an access-control incident; avoid further access, preserve a redacted request ID and timestamp, revoke affected sessions, investigate signature verification and FORCE RLS. Never post another user's content publicly.

## Memory cannot be approved

Check source message ownership, candidate state, revision/If-Match, feature flag, migration 4, and the response code. A stale revision can legitimately produce a conflict. Never insert active memories directly into PostgreSQL as a workaround.

## Agent appears stuck

Separate HTTP authentication, API accepted task, worker queue/run state, model-gateway failure and external tool authorization. Trace run IDs and observed timestamps; never assume a color indicator means a model ran. Validate cancellation and timeouts.

References: [live release gates](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md) and [runtime architecture](https://github.com/nyameko/agent-control-plane/blob/main/docs/07-runtimes-harnesses-and-sandboxes.md).