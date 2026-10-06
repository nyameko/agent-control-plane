# 2. Reference architecture

## 2.1 Architectural statement

ACP is the **durable context, policy and coordination plane** between user-facing clients and replaceable agent/model/execution systems.

It is deliberately positioned above runtimes and below product surfaces.

~~~text
+---------------------------- CLIENTS --------------------------------+
| Quantum Platform | Jupyter | SSH/TUI | gptel | API | future chat    |
+--------------------------------+------------------------------------+
                                 |
                    authenticated delegated identity
                                 |
                                 v
+---------------------- AGENT CONTROL PLANE --------------------------+
| identity context | tenancy | policy | approvals                     |
| projects | conversations | memory | skills                          |
| tasks | runs | events | audit | artifacts/references                |
| runtime selection | logical model pools | execution contracts       |
+---------+----------------------+----------------------+--------------+
          |                      |                      |
          v                      v                      v
   meta/orchestration      runtime adapters      execution brokers
      Paperclip             Hermes               Kubernetes
      later strategies      LangGraph            OpenStack
                            Letta                Slurm
                            PydanticAI           quantum-workflows
                            Agent Framework      QPU/provider
                            OpenHands
                            Goose / smolagents
          |                      |
          +----------+-----------+
                     |
                     v
                 model gateway
             vLLM | Ollama | llama.cpp
                     |
                     v
           open weights / authorised APIs

+----------------------------- STATE ---------------------------------+
| ACP PostgreSQL | runtime PVC/cache | Git | project/artifact storage |
| secret broker  | metrics/logs/traces | scheduler/provider records  |
+--------------------------------------------------------------------+
~~~

## 2.2 The three planes

### Product/client plane

Quantum Platform, Jupyter, editor integrations and terminal clients present the user's work. They do not own canonical agent state.

### Agent control plane

ACP owns the portable records required to reconstruct authorised context and coordinate agent work.

### Execution/resource plane

Runtimes, model servers, sandboxes, Kubernetes, Slurm and QPU providers execute work. They retain their own authoritative local state where appropriate, but ACP records references and provenance.

## 2.3 Canonical state

The canonical ACP record includes, as milestones mature:

- external principal/tenant references;
- minimal and later rich projects;
- conversations and messages;
- memory items and provenance;
- skill bindings and versions;
- tasks, runs, events and delegation lineage;
- approvals;
- runtime/profile/session mappings;
- model-routing decisions;
- artifact references;
- external execution references.

Canonical does not mean ACP duplicates every external system.

For example, ACP stores a Slurm job ID and status observations; Slurm remains authoritative for the job.

## 2.4 Portable context assembly

The core abstraction is not a Hermes session or a model-provider conversation ID. It is a portable run context:

~~~text
AgentRunContext
├── principal
│   ├── AgentPrincipal subject
│   ├── tenant / programme
│   └── delegated capabilities
├── project context
├── conversation messages
├── retrieved memory items
├── enabled skill definitions
├── task/run history summary
├── runtime policy
├── logical model pool
├── execution allowances
└── correlation identifiers
~~~

The runtime adapter translates this into the native representation required by Hermes, Letta, LangGraph, Agent Framework, OpenHands or another runtime.

The result is normalised back into ACP records.

## 2.5 Normalised runtime contract

A runtime adapter should eventually expose operations equivalent to:

~~~text
capabilities()
start(context)
resume(context, runtime_reference)
send(input)
stream_events()
request_tool()
pause_for_approval()
stop()
health()
version()
export_runtime_metadata()
~~~

Portable state belongs in ACP. Runtime-specific details remain namespaced metadata.

## 2.6 Request lifecycle

A mature request follows this path:

1. A client authenticates through Quantum Platform or an approved delegated flow.
2. ACP validates principal, tenant/programme and requested capability.
3. ACP loads the canonical project/conversation state.
4. ACP retrieves only authorised memory and skill context.
5. Policy produces the candidate runtime, model-pool and execution envelope.
6. An optional meta-orchestrator such as Paperclip chooses among allowed specialists.
7. The runtime adapter receives a bounded AgentRunContext.
8. The runtime reasons and emits normalised events/tool requests.
9. Every privileged tool request is re-authorised at the boundary.
10. Heavy work is submitted to the authoritative execution system.
11. Final messages, events, routing decisions and external references are committed to ACP.
12. Scientific results remain in quantum-workflows/artifact storage and are linked by provenance.

## 2.7 Failure semantics

A central architectural requirement is that ordinary process loss does not imply context loss.

~~~text
browser dies              -> reconnect
Jupyter Pod is culled      -> reconnect
SSH session disconnects   -> reconnect
ACP API restarts          -> reload PostgreSQL
agent worker restarts     -> reconstruct context
Hermes session disappears -> start a replacement runtime session
model endpoint fails      -> policy-valid fallback or explicit failure
Slurm controller owns job -> ACP reconciles by external job reference
~~~

If PostgreSQL containing canonical ACP state is unavailable, new stateful work stops rather than silently falling back to anonymous runtime-local history.

## 2.8 State versus cache

A useful test is:

> Could we delete this runtime/Pod/client and still reconstruct the user's authorised work?

If the answer is no, the supposedly replaceable component owns state that has not yet been promoted into the proper canonical system.

## 2.9 Identity boundary

Quantum Platform is authoritative for human identity.

ACP consumes an immutable AgentPrincipal UUID as its stable subject. POSIX UID/GID, usernames and email addresses are linked attributes, not the ACP identity key.

This allows:

- UID/GID policy changes;
- federation;
- username changes;
- multiple execution environments;
- runtime replacement;

without changing ownership of agent state.

## 2.10 Meta-orchestration boundary

Paperclip or another meta-harness can coordinate specialists, but it does not own:

- user identity;
- canonical conversation history;
- memory;
- skill grants;
- approvals;
- platform capabilities;
- scheduler authority.

This keeps meta-orchestration replaceable too.

## 2.11 Initial and future deployment

Today the repository has a narrow administrative API/worker/PostgreSQL/Hermes slice.

M4 adds the personal-agent continuity path.

Later deployment may contain:

~~~text
Kubernetes namespace: agent-control-plane
├── API replicas
├── policy/context services
├── worker/runtime adapter pools
├── optional Paperclip coordinator
├── model gateway client
└── network policies

ACP PostgreSQL
├── canonical conversations
├── memory/projects/skills
├── tasks/runs/events
└── runtime/execution references

Retained runtime storage
└── optional per-user/project runtime profiles

External execution
├── Kubernetes Jobs
├── OpenStack sandboxes
├── Slurm CPU/GPU
├── quantum-workflows
└── QPU/provider brokers
~~~

The isolated administrative/orchestrator VM can remain an out-of-band diagnostic/federation root. It must not become a second canonical conversation database.
