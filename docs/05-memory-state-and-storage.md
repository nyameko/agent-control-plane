# 5. Memory, state and storage

## 5.1 The governing rule

Every state class needs one canonical owner.

ACP owns **canonical agent context**. Runtime-native databases, caches and checkpoints are secondary representations.

## 5.2 State ownership

| State | Canonical owner/store | Notes |
| --- | --- | --- |
| human identity, programmes, entitlements | Quantum Platform PostgreSQL | ACP stores stable external subject references |
| ACP project/conversation/message state | ACP PostgreSQL | canonical cross-client history |
| ACP memory and skill bindings | ACP PostgreSQL + reviewed Git references | introduced after M4a |
| tasks/runs/events/approvals/routing decisions | ACP PostgreSQL | durable operational lineage |
| Hermes/other runtime session/cache/profile | runtime-local persistent or ephemeral storage | accelerates continuity; never sole record |
| reviewed agent definitions/policies/shared skills | Git | immutable/versioned source |
| user/project files | research home/project storage | NFS/parallel/object storage as appropriate |
| large artifacts | object/artifact storage | referenced by digest/URI from ACP |
| scientific result provenance | quantum-workflows | ACP stores correlation/reference |
| Slurm/QPU execution state | scheduler/provider | ACP stores external references and observations |
| embeddings/index | derived store, initially PostgreSQL/pgvector if useful | rebuildable from authorised canonical sources |
| secrets | secret broker/Sealed Secrets/Vault-class system | never durable prompt/memory content |
| telemetry | Prometheus/log/trace backends | bounded operational retention |

## 5.3 PostgreSQL ownership

ACP's database belongs to `agent-control-plane`.

It may physically share PostgreSQL infrastructure with another service in the future, but logical ownership, roles, migrations and credentials remain separate.

ACP PostgreSQL stores:

- stable external identity/tenant references;
- projects and conversations;
- messages;
- memory items and provenance;
- skill bindings;
- task/run/delegation history;
- runtime/session/profile mappings;
- tool and approval records;
- model/compute routing decisions;
- artifact and scheduler references;
- retention/export metadata.

It does not store:

- passwords;
- raw provider secrets;
- model weights;
- full repository mirrors;
- large binary artifacts when object/project storage is more appropriate.

## 5.4 Conversation history is not memory

A transcript records what happened.

Memory is a derived, purpose-specific item that may be retrieved later.

M4a implements canonical conversation continuity. M4b adds explicit memory.

~~~text
message / tool evidence / run result
                 |
                 v
          memory candidate
                 |
      policy + provenance
       + optional confirmation
                 |
                 v
         durable memory item
                 |
                 v
          derived retrieval index
~~~

Deleting/correcting a source must invalidate affected derived state.

## 5.5 Memory classes

- **working context** — transient context used for one run;
- **episodic memory** — durable summary of an experience/task/run;
- **semantic memory** — durable facts/relationships with provenance;
- **preferences** — explicit user preferences, not inferred sensitive attributes;
- **procedural knowledge** — reusable methods/skills, usually governed as skills rather than arbitrary memory.

A private user's memory must not silently become programme/institutional memory.

## 5.6 Projects

M4a uses only a minimal durable project stub.

M4c makes Project a full first-class context linking:

- members/roles;
- repositories;
- conversations;
- memory scopes;
- skills;
- workspaces/artifacts;
- workflow and execution history.

Keeping the M4a representation minimal prevents the first persistence milestone from becoming a workspace-management project.

## 5.7 Skills

Skills are versioned procedural definitions with declared authority and provenance.

Shared skills should be reviewed in Git when practical. ACP records which version is enabled for which user/project/agent.

Runtime-local skill material may be generated/mounted from those canonical bindings.

## 5.8 Runtime state

Hermes and other frameworks may maintain:

- native sessions;
- checkpoints;
- local memories;
- indexes;
- profile configuration;
- caches.

Those are useful.

They are not the portable platform record.

The key failure test is:

> If this runtime profile is destroyed, can ACP reconstruct enough authorised context for the user to continue?

M4a requires the answer to be yes for conversation continuity.

M4e later makes Hermes-native profile persistence richer without reversing that ownership rule.

## 5.9 Cinder and runtime PVCs

A retained Cinder RWO volume protects runtime state from normal Pod replacement. It does not create a shared multi-client database, and it is not a backup.

Portal, Jupyter, SSH and runtime workers should share history through authenticated ACP APIs, not by mounting the same block volume everywhere.

## 5.10 Artifacts and research files

ACP should store metadata/digests and references rather than force large artifacts into relational tables.

Use:

- project/research storage for working datasets/files;
- object/artifact storage for immutable large outputs;
- Git for source and reviewed declarative definitions;
- quantum-workflows manifests for reproducible scientific outputs.

## 5.11 Retention, export and deletion

Durable does not mean immortal.

Users need explicit:

- archive;
- export;
- delete;
- correction;
- memory invalidation;
- retention policy.

Exports should use portable documented formats rather than dumping an opaque runtime profile directory.

## 5.12 ACP state taxonomy

Keep these state classes distinct even when they are related:

1. **Conversation history** — what was said.
2. **Durable agent memory** — what should be remembered.
3. **Knowledge/RAG corpora** — documents, repositories, papers and manuals.
4. **Projects/workspaces** — what work belongs together.
5. **Artifacts/evidence** — files, outputs, patches, reports and results.
6. **Tasks/runs/tool events** — what the agent actually did.
7. **Skills** — governed reusable procedures.
8. **Persona/runtime configuration** — SOUL/profile/preferences/runtime settings.
9. **External execution references** — Slurm job IDs, Kubernetes jobs, QPU jobs and workflow IDs.
10. **Imported archives** — historical ChatGPT, Claude, DeepSeek and other provider exports.
11. **Evaluation/provenance** — model/runtime/revision/quality/evaluation results.
12. **Secrets/credentials** — never conversation, memory or RAG content.

The boundaries are deliberate:

- skills are not memories;
- projects are not conversations;
- artifacts are not memories;
- imports are not memories;
- runtime-native state is not canonical memory;
- RAG documents are not memories;
- credentials are never prompt/history data.

## 5.13 Historical chat import/export

M4a starts with fresh canonical conversations, fresh run history and fresh ACP state.

Historical provider exports should be introduced later as **imported archives**, not automatically promoted into memory.

~~~text
provider export
      |
      v
immutable/raw import artifact
      |
      v
normalised imported conversation/messages
      |
      v
optional memory candidates
      |
policy/provenance/user review
      |
      v
canonical durable memory
~~~

An import record should retain provider, export format/version, original conversation/message identifiers and timestamps, import checksum, source artifact reference and import status.

This prevents stale architecture, hallucinations, obsolete credentials/configuration references and contradictory historical statements from silently becoming durable memory.

Exports from ACP should use documented portable formats with stable identifiers and provenance.

## 5.14 Vector retrieval progression

The vector-search roadmap is intentionally incremental:

~~~text
M4a
conversation continuity
PostgreSQL only
NO vector database

        |
        v

M4b
canonical durable memory
PostgreSQL
+
pgvector as a rebuildable derived retrieval index

        |
        v

M4c
projects / knowledge scopes
pgvector initially

        |
        v

measured scale threshold
        |
        +--> keep pgvector
        |
        +--> dedicated vector service
             Milvus / Qdrant / equivalent
~~~

A vector index is never the canonical memory store. Embeddings must retain model/revision/dimensions/content-hash metadata and be regenerable from authorised canonical sources.

Move to a dedicated vector service only after measurements demonstrate a real need, such as unacceptable pgvector latency, operationally painful index size, materially higher concurrency, a corpus far larger than ACP relational state, or a need to scale knowledge retrieval independently.
