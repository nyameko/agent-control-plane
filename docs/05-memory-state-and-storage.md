# 5. Memory, state and storage

## 5.1 The core distinction

“Memory” is not one database or one mounted directory. The platform needs several state classes
with different retention, portability, consistency and security requirements.

| State | Canonical store | Examples | Backup/retention |
| --- | --- | --- | --- |
| relational control state | PostgreSQL | conversations, messages, tasks, runs, approvals, routing decisions, jobs, audit indices | PITR, explicit retention |
| mutable runtime profile | Cinder-backed PVC | Hermes config, runtime session cache, local skills, runtime checkpoints | encrypted volume snapshot; not sole system record |
| workspace | per-user/project PVC or ephemeral volume | Git worktrees, notebooks, temporary datasets, build caches | quota; snapshot only when valuable |
| large immutable artifact | S3-compatible/object store when available; transitional Cinder service volume | logs, attachments, patches, reports, model outputs, scientific artifacts | digest, lifecycle policy, legal retention |
| declarative shared definition | Git | agent templates, `SOUL` sources, reviewed skills, policies, schemas, evals | normal Git history/review |
| embeddings/index | PostgreSQL + pgvector initially | derived retrieval vectors and chunk metadata | rebuildable from authorised sources |
| secret | Vault/KMS/HSM eventually; encrypted broker now | provider tokens, bot tokens, wrapping keys | rotation and access audit; never model context |
| operational telemetry | Prometheus/log/trace backend | latency, queue depth, token/compute usage | bounded operational retention |

## 5.2 PostgreSQL placement

The first production deployment can use the same PostgreSQL cluster as `quantum-platform`, but it
should use a **separate database, role and credential**. Sharing a server is operational reuse;
sharing every table and database privilege is coupling.

The control-plane database stores:

- external identity/tenant references, not passwords;
- canonical cross-client conversation/message history;
- tasks, attempts, delegations and run state;
- tool calls and redacted inputs/outputs or artifact references;
- model and compute routing decisions with reasons;
- approvals and immutable audit events;
- channel bindings and user retention preferences;
- pointers/digests for large artifacts and runtime profiles.

Large binary data, full repository copies, model weights and plaintext credentials do not belong in
PostgreSQL.

## 5.3 Conversation history is not long-term memory

The canonical message log preserves what was said. Long-term memory is a derived, purpose-specific
record that may be retrieved in future conversations.

Promotion flow:

```text
message/tool evidence
       │
       ▼
candidate memory + provenance + sensitivity
       │
 policy / optional user confirmation
       │
       ▼
versioned memory item
       │
 embedding/index (derived and rebuildable)
```

Deleting or correcting a source must invalidate derived memories and indexes. An agent may propose
memory; it should not silently convert every private conversation into permanent institutional
knowledge.

## 5.4 Memory layers

- **Working memory:** current context and scratchpad; short-lived, runtime-specific.
- **Episodic memory:** a task/run summary with outcome and evidence.
- **Semantic memory:** durable facts and relationships with provenance and sensitivity.
- **Procedural memory:** skills, playbooks and tested workflows.
- **Identity/preferences:** user-provided preferences, never inferred sensitive attributes without
  a legitimate purpose.

Shared procedural memory is promoted into reviewed Git. User-specific procedural adaptations stay
private unless the user explicitly shares them.

## 5.5 Souls and agent definitions

Treat a soul as versioned behaviour configuration, not a mystical opaque file:

```text
agent definition
├── purpose and non-goals
├── base system/SOUL content
├── capability references
├── model-pool policy
├── runtime/harness adapter
├── skill bundle digests
├── memory scopes
└── evaluation suite
```

Shared definitions live in Git. At run start the control plane stores the Git revision and a
content digest. Per-user runtime material is mounted into Hermes from a Cinder PVC, but the durable
run record references the versioned definition that produced it.

## 5.6 Hermes state

Hermes currently keeps configuration, soul, memories, skills, cron, sessions, logs and a SQLite
state database under its profile directory. Mounting that directory on a Cinder PVC provides
runtime continuity, but the multi-user platform must not treat one shared SQLite database as its
canonical conversation service.

Use one of two controlled patterns:

1. one isolated Hermes profile/PVC per user, project or agent principal; or
2. ephemeral Hermes workers hydrated from the control plane and writing canonical events back.

The first is simpler for early persistent personal agents; the second scales better. Both require
an adapter that maps control-plane task/run IDs to Hermes session IDs.

## 5.7 Research data and collaboration discovery

Research queries, saved searches, literature annotations and collaboration candidates belong to
the tenant/user's control-plane records and artifact store. The collaboration agent may compare
only scopes for which sharing is authorised. A match should explain the evidence and allow both
parties to opt in; it must not expose private proposals or conversations to create a match.

## 5.8 Retention and portability

Users need controls to export, archive and delete conversations and memories subject to legitimate
audit or research-retention constraints. Export should include portable JSON plus artifact digests,
not an undocumented copy of a Hermes directory.
