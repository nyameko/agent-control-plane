# Integration status and future trajectory

This document is a status/reconciliation note. The authoritative design lives in docs 01–11 and the ADRs.

## Current repository relationship

The four repositories form one platform with intentionally different authorities:

~~~text
quantum-platform
  identity + researcher product
          |
          v
agent-control-plane
  durable agent context + policy + runs
          |
          +------> runtime/model layer
          |
          +------> bounded execution contracts
                         |
              +----------+----------+
              |                     |
        infra-hpc-qc-k8s     quantum-workflows
        deployment/schedulers scientific execution/provenance
~~~

## Current ACP implementation

The executable v0.2/Phase-1 slice is still intentionally small:

- private administrator identity assertion;
- one fixed read-only diagnostic;
- PostgreSQL task/run/event ledger;
- bounded Hermes explanation;
- persistent administrative runtime volume;
- tenant isolation and constrained network access.

That slice proves plumbing and authority boundaries. It is not the final personal-agent architecture.

## M4 transition

M4 changes the centre of gravity from an administrative diagnostic to durable user context.

The key ownership correction is:

| Data | Canonical owner |
| --- | --- |
| Human account/programme | Quantum Platform |
| AgentPrincipal UUID | Quantum Platform |
| POSIX UID/GID | Quantum Platform provisioning/execution identity |
| Personal project/conversation/message | ACP |
| Memory/skill bindings | ACP |
| Runtime-native session/cache/profile | runtime |
| Task/run/event history | ACP |
| Scientific result/provenance | quantum-workflows |
| Physical job state | Slurm/provider |
| Infrastructure desired state | infra-hpc-qc-k8s/GitOps |

This supersedes older notes that placed future personal chat/memory in a separate Quantum Platform user-data service.

Quantum Platform presents and authenticates the experience; ACP owns the portable agent context.

## Workbench-first model

Jupyter remains a client.

Deleting/recreating a Jupyter Pod must not affect the canonical conversation.

Heavy CPU/GPU/QPU execution is requested through bounded platform/workflow contracts rather than turning the notebook or agent runtime into the scheduler.

## Runtime trajectory

Hermes is first.

Later adapter candidates can include LangGraph, Letta, PydanticAI, Microsoft Agent Framework, smolagents, OpenHands, Goose and future specialist runtimes.

Paperclip is evaluated as a meta-orchestration strategy over those runtimes.

Neither runtime nor meta-orchestrator owns canonical ACP state.

## Model trajectory

The present single explicit model route evolves into logical model pools backed by:

- local/workstation serving;
- A100/H200 inference services;
- open-weight models;
- explicitly authorised external providers.

Routing reasons, resolved models and usage become durable run metadata.

## Infrastructure trajectory

The runtime fabric can expand from the existing Kubernetes/CPU Slurm baseline to:

- isolated engineering sandboxes;
- A100/H200 model-serving pools;
- accelerated Slurm jobs;
- multi-node/MPI;
- remote H200/Axis-style access providers;
- QPU provider brokers.

Schedulers remain authoritative.

## Security trajectory

The biggest new M4 risk is persistence of private user context.

Before expanding autonomy, prove:

- subject + tenant isolation;
- no cross-user enumeration;
- no runtime-only canonical state;
- explicit memory provenance;
- secret exclusion;
- auditable privileged access;
- scoped delegated capabilities.

## Acceptance culture

The platform keeps a distinction between:

- source/manifest present;
- service healthy;
- end-to-end user capability accepted.

M4a therefore ends with the destructive continuity test, not merely with tables and endpoints.
