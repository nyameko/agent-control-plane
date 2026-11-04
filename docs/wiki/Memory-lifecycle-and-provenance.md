# Private memory, revisions and source provenance

## Why memory is not a chat summary

Personal memory is durable, inspectable **state**, not a model's informal guess, an automatically trusted chat digest, or the only copy of a research notebook. ACP stores candidate memory items and immutable revision history in PostgreSQL; the user's source messages and consent/approval must be linked. Retrieval should respect ownership, verification, scope, expiry, sensitivity and current approval status.

## Proposed and implemented contract boundary

The v4 memory schema is declared in the source migration history and the API registers candidate, list, retrieve, approve, correct and revoke operations. Availability in a **live** deployment is contingent on v4 migration, enabled feature settings and passed authorization tests. The M4b contract doc was originally a proposal; inspect the latest source and release evidence before claiming an operation works for a user.

The intended state machine is:

```text
source user message -> candidate rev 1 -> explicit approve -> active rev 2
                                              |             |
                                           correction    revocation
                                           active rev N   revoked rev N
```

Revisions preserve meaningful audit history. An active memory that expires should cease retrieval without inventing a new user-approval event. Revoked or unverified assertions should not be supplied to a model as current authoritative truth.

## User workflow

Review the proposed memory text, source conversation, author and why it is considered useful. Remove secrets, patient data, personal identifiers or hallucinated facts. Approve only accurate, relevant and permitted content. Correct with an explicit new version; revoke if it should no longer be supplied as context. A memory review action should never accept a guessed cross-user memory UUID.

## Concurrency, reproducibility and safety

Mutation APIs should use idempotency keys and revision matching when documented, and return a conflict rather than overwriting a simultaneous edit. Retain source hashes and scientific references but don't mistake hashes for external evidence that a claim is true. A user choosing to delete sensitive memory may require an additional controlled purge/retention policy beyond ordinary revocation.

See [memory contract](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4b-MINIMAL-MEMORY-CONTRACT.md), [memory implementation](https://github.com/nyameko/agent-control-plane/blob/main/src/agent_control_plane/memory.py), [ADR 0009](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0009-m4b-minimal-canonical-memory.md).