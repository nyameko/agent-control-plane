# M4 — Persistent Personal Agent

M4 is the milestone where Agent Control Plane stops being only an administrative agent slice and becomes a durable personal research-agent substrate.

The milestone is intentionally sequenced. **M4a stays small.**

## M4 sequence

~~~text
M4a — Persistent Personal Agent
      canonical conversation continuity

M4b — Memory
      explicit durable memory + provenance + retrieval

M4c — Projects
      full project/workspace model

M4d — Skills
      governed skill catalogue + enablement

M4e — Persistent Hermes Profiles
      richer native runtime/persona/profile continuity

M4f — Quantum Platform Guide
      ubiquitous researcher-facing agent UI

M4g — SSH Enterprise Client
      attach/resume/create conversations from terminal
~~~

Do not collapse these into one large feature.

## M4a — Persistent Personal Agent

### Purpose

M4a proves exactly one thing:

> A user's project/conversation and its canonical history survive the loss of clients and agent runtime processes.

M4a does **not** implement the full memory system, rich project workspaces, skill catalogue, persistent user-specific Hermes persona, Paperclip orchestration or accelerated model routing.

### Minimal canonical model

M4a may create a minimal project stub only so a conversation has a durable grouping key.

The durable core is:

~~~text
AgentPrincipal subject
        |
        v
minimal project
        |
        v
conversation
        |
        +-- messages
        +-- task/run references
        +-- runtime/session correlation
~~~

The richer meaning of Project belongs to M4c.

### Identity

The owner is the Quantum Platform AgentPrincipal UUID expressed as the ACP external subject.

POSIX UID/GID is not used as the conversation owner key.

### Runtime rule

Hermes is the first runtime adapter.

Hermes SQLite/session/profile state may help resume efficiently, but M4a must remain correct if the personal runtime session/cache is destroyed.

The worker reconstructs sufficient context from ACP's canonical PostgreSQL state.

### Manual acceptance drill

The first acceptance test is deliberately destructive.

1. Log into quantum.nyameko.com.
2. Create project **M4 Persistence Test**.
3. Start conversation **Persistence Drill**.
4. Give the agent a unique marker such as **ACP-PERSIST-7F31**.
5. Receive a response and record project/conversation UUIDs.
6. Close the browser completely.
7. Launch Jupyter and attach to the same conversation.
8. Stop and delete the Jupyter user Pod.
9. Disconnect SSH sessions.
10. Restart/delete the personal agent worker.
11. Preferably remove its ephemeral runtime session/cache.
12. Reopen the conversation from another supported surface.
13. Verify the same project UUID and conversation UUID.
14. Verify the same canonical transcript and task/run history.
15. Ask what marker was provided earlier and require recovery of **ACP-PERSIST-7F31** from canonical history.
16. Verify a second user cannot list, retrieve or attach to the conversation.
17. Restart the ACP API and repeat retrieval.

### Permanent automated conformance test

Once the vertical slice exists, the manual drill becomes a permanent release gate.

The automated test must prove at least:

~~~text
client-local state deleted       -> history survives
new HTTP/API process             -> history survives
worker process replacement       -> history survives
runtime-local session loss       -> next turn can be reconstructed
different authorised surface     -> same conversation
different user                   -> cannot enumerate/read/append
ACP API restart                  -> same canonical state
~~~

Later conformance can extend to backup/restore and database failover.

### Definition of done

M4a is complete only when:

- project/conversation IDs are durable;
- messages are canonical in ACP PostgreSQL;
- personal APIs are subject/tenant isolated;
- user-message ingestion is idempotent;
- a worker can rebuild the next turn from canonical context;
- assistant output is committed back to canonical history;
- task/run lineage survives runtime replacement;
- the destructive manual acceptance drill passes;
- the equivalent automated conformance test runs in CI/staging;
- existing administrative Phase-1 APIs remain compatible.

## M4b — Memory

M4b adds explicit durable memory.

Conversation history is not memory.

Memory classes include:

- episodic task/run summaries;
- semantic facts/relationships;
- explicit user preferences;
- project knowledge;
- reusable procedural knowledge where appropriate.

Every memory item needs provenance, scope, sensitivity, lifecycle and invalidation/correction semantics.

Promotion is explicit:

~~~text
conversation / tool / run evidence
                |
                v
         memory candidate
                |
       policy / confirmation
                |
                v
      durable memory item
~~~

Derived embeddings/indexes are rebuildable and are not the canonical memory record.

## M4c — Projects

M4c turns the M4a project stub into a full research/engineering workspace model:

~~~text
Project
├── owner / members / programme
├── repositories
├── conversations
├── memory scopes
├── enabled skills
├── workspace and artifact references
├── tasks / runs
├── workflow executions
└── execution/provenance history
~~~

Projects should work for software engineering, HPL optimisation, quantum simulation, literature work, teaching and research programmes without being tied to one agent runtime.

## M4d — Skills

Skills become governed procedural capabilities.

A skill has:

- stable identifier and version;
- source and provenance;
- declared inputs/outputs;
- required capabilities;
- runtime compatibility;
- review/trust status;
- optional evaluation suite.

Shared skills should normally be reviewed/versioned in Git. Private skill adaptations remain user/project scoped.

Skills are not hidden prompt fragments with implicit authority.

## M4e — Persistent Hermes Profiles

Only after canonical state is proven do we make the Hermes-native personal experience richer.

Persistent Hermes profiles may add:

- user/project SOUL/persona configuration;
- runtime-native memory/cache;
- local skill materialisation;
- native session checkpoints;
- runtime preferences;
- native indexes.

ACP continues to own portable state and runtime mappings.

Destroying the Hermes profile may reduce convenience/performance, but must not erase the canonical project/conversation/memory record.

## M4f — Quantum Platform Guide

Quantum Platform gains an ubiquitous Guide/co-scientist surface backed by ACP.

It can:

- explain the platform;
- continue project conversations;
- guide environment/workflow use;
- surface authorised run history;
- explain logical execution offerings;
- interpret workflow manifests/results;
- assist with research and engineering work according to capabilities.

It does not become an infrastructure superuser simply because it is visible everywhere.

## M4g — SSH Enterprise Client

The terminal becomes another ACP client rather than another isolated chat history.

The user can:

- list/select projects;
- list/create/resume conversations;
- inspect runs;
- submit messages;
- attach to approved workflows;
- launch the normal shell.

Conceptually:

~~~text
+------------- QUANTUM PLATFORM -------------+
| Project       HPL optimisation             |
| Conversation  Performance investigation    |
| Workbench     running                      |
| Runs          2 active                     |
| Agent         connected                    |
|                                            |
| Agent | Projects | Runs | Shell            |
+--------------------------------------------+
~~~

Herdr or other terminal tooling can improve session ergonomics, but it does not become the source of identity or canonical conversation state.

## After M4

M4 establishes the durable substrate required for broader orchestration:

~~~text
Paperclip
├── Hermes
├── Herdr-integrated workers
├── coding agents
├── security agents
├── storage agents
├── research agents
└── specialist harnesses
        |
        v
A100 / H200 inference fabric
        |
        v
model routing / evaluation / quotas
        |
        v
Slurm accelerated execution
        |
        v
QPU orchestration
~~~

The order matters. Advanced orchestration becomes much easier once every participant receives the same canonical context.
