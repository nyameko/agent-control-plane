# Architecture and state ownership

## Why ACP is separate

A model predicts content; a harness executes a reasoning/tool loop; a scheduler allocates resources; an identity provider issues trust; and ACP stores durable project context. These are independent components. ACP must remain usable when an individual model, agent worker, UI tab or Jupyter Pod disappears.

```text
Quantum Platform login/programme policy
         | signed AgentPrincipal assertion
         v
ACP API / PostgreSQL -- canonical projects, conversations, messages,
         |              memories, revisions, profiles, task/run references
         +---- approved runtime adapter (Hermes first; others pluggable)
         |                   |
         |                model gateway / local GPU inference
         |
         +---- typed integration requests -> Quantum Platform
                                          -> Slurm/provider scheduler
                                          -> Quantum Workflows results
```

## Authoritative systems

| State | Owner |
|---|---|
| Human account, institution, programme, entitlements | Quantum Platform |
| ACP external principal identity | signed AgentPrincipal UUID |
| Projects, conversation/message history, memory revisions and personal profile | ACP PostgreSQL |
| Runtime-native sessions, checkpoints, personas | runtime-local secondary cache |
| Portable shared policy/skills | reviewed Git revisions |
| HPC/QPU allocation and state | Slurm or hardware provider |
| Scientific data/provenance | Quantum Workflows / science library |
| Resource files and secrets | protected storage and secret custody |

A POSIX UID, SSH username or a caller-supplied `tenant` field is **never** sufficient proof of ACP conversation ownership. A model is never an IAM authority. RLS, signed authentication and scoped authorization guard data on the server.

## Milestone boundaries

M4a: canonical cross-client personal conversation continuity. M4b: private memory and source/revision lineage. M4c: richer projects and authorised programme rooms. M4d: governed scientific skill references. M4e: portable profile and harness continuity. M4f: browser Guide integration and passive observed status. M4g: terminal/SSH client integration with a trusted pairing broker. **A contract written in an ADR is not proof that the endpoint or broker is deployed.**

See [state architecture](https://github.com/nyameko/agent-control-plane/blob/main/docs/05-memory-state-and-storage.md), [routing](https://github.com/nyameko/agent-control-plane/blob/main/docs/06-model-and-compute-routing.md), [ADR 0008](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0008-agentprincipal-not-posix-identity.md) and [ADR 0012](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0012-portal-mediated-terminal-authentication.md).