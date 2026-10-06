# 7. Runtimes, harnesses, meta-orchestration and sandboxes

## 7.1 Separate the layers

Do not use "agent", "model" and "runtime" as synonyms.

| Layer | Examples | Responsibility |
| --- | --- | --- |
| model weights/provider | Qwen, DeepSeek, Mistral, gpt-oss, other local/external models | generation/reasoning |
| inference runtime/server | vLLM, Ollama, llama.cpp | serve models |
| agent runtime/harness | Hermes, LangGraph, Letta, PydanticAI, Agent Framework, smolagents, OpenHands, Goose | agent loop, native sessions, tool protocol, workflow semantics |
| meta-orchestrator | Paperclip or future coordinator | select/coordinate allowed specialist runtimes |
| execution environment | container, OpenStack sandbox, Kubernetes Job, Slurm allocation, QPU provider | execute code/scientific work |
| control plane | ACP | canonical context, identity references, policy, run/audit history, portable contracts |

One physical task may span every row.

## 7.2 Hermes first, not Hermes forever

Hermes is the first full runtime integration because it provides a useful agent loop, sessions, skills/memory/profile concepts and programmable integration.

ACP maps portable identifiers to Hermes-native ones:

~~~text
ACP principal/project/conversation/task/run
                   |
                   v
       Hermes profile/session/run
~~~

Hermes does not become the source of Quantum Platform identity or ACP canonical conversation history.

M4a must remain correct even if runtime-local session/cache state is lost.

M4e later makes persistent Hermes profiles a richer optimisation/user experience.

## 7.3 Other runtime/harness options

ACP should remain compatible with multiple styles of runtime.

### LangGraph

Useful where explicit graph/state-machine orchestration and durable execution/checkpoint concepts are valuable.

### Letta

Useful for experimenting with strongly stateful/memory-centric agents.

Letta-native memory is runtime state from ACP's perspective unless explicitly promoted through ACP's memory contract.

### PydanticAI

Useful for typed Python agent applications, structured outputs and model-provider portability.

### Microsoft Agent Framework

Useful for agent/workflow orchestration and heterogeneous provider integration. It can be evaluated as a runtime/workflow adapter rather than a replacement for ACP.

### Hugging Face smolagents

Useful for compact research/specialist agents and experiments with local/open model backends.

### OpenHands

Useful as a specialised software-engineering/coding runtime, particularly when paired with isolated workspaces/sandboxes.

### Goose

Useful for developer/terminal-oriented agent workflows and extension-driven tooling.

### Simple ACP-native workers

Not every task needs a framework. A deterministic worker or direct-model adapter can be safer and easier to operate for narrow capabilities.

## 7.4 Paperclip boundary

Paperclip is a planned meta-harness/meta-orchestration layer.

Its role is potentially:

- select a specialist runtime/agent;
- coordinate multiple specialists;
- manage higher-level task decomposition;
- compare/review candidate work;
- route between available harnesses.

Its role is **not**:

- canonical database;
- identity provider;
- memory authority;
- policy authority;
- scheduler;
- secret store.

Conceptually:

~~~text
                 Paperclip
        meta coordination / routing
                     |
                     v
             Agent Control Plane
        context + policy + durable state
                     |
     +---------------+----------------+
     |               |                |
   Hermes        OpenHands          Letta
   LangGraph     Goose              PydanticAI
   Agent FW      smolagents         future adapters
~~~

If implementation constraints later require Paperclip to call ACP rather than sit logically above it, the authority boundary stays the same: ACP remains the durable state/policy substrate.

## 7.5 Herdr, Herder and developer supervision

Herdr can supervise interactive/local/remote terminal agents and is useful developer ergonomics.

A Herder-style queued CLI supervisor may be useful when ACP needs a bounded external worker fleet.

Neither should silently introduce a second authoritative task ledger. Adapter IDs and status must correlate back to ACP task/run records.

## 7.6 Heretic

Heretic belongs to model engineering/weight modification and evaluation.

A modified model must be registered as a distinct model artifact with provenance, licence, evaluation and policy metadata.

It is not an agent memory/orchestration system.

## 7.7 Adapter contract

Every runtime adapter should converge on portable operations such as:

- capability discovery;
- start/resume/stop;
- submit input;
- stream normalised events;
- tool/approval translation;
- artifact/reference attachment;
- usage/result/error reporting;
- runtime version/health;
- export of runtime-session correlation.

Runtime-specific fields remain extensions rather than leaking into every client.

## 7.8 Context hydration

ACP assembles the authorised context before runtime execution.

A runtime should not need direct unrestricted database access.

It receives only the slice required for the task:

~~~text
principal + tenant
project
conversation
retrieved memory
enabled skills
task/run context
capabilities
logical model choice
execution allowances
~~~

This is the core mechanism for runtime/harness agnosticism.

## 7.9 Sandboxes

Arbitrary generated commands must never run inside ACP API/worker containers.

A sandbox request declares:

- subject/project/task/run;
- immutable source commit;
- writable worktree/branch;
- image digest;
- CPU/memory/GPU/disk/time limits;
- egress policy;
- allowed secret references;
- command/tool family;
- artifact contract;
- lease/heartbeat/cleanup.

The broker returns an opaque execution ID. The sandbox never receives ACP database-owner credentials.

## 7.10 Repository modification workflow

~~~text
approved source revision
       |
isolated worktree/sandbox
       |
agent change + tests
       |
patch / agent/* branch
       |
CI + human/agent review
       |
authorised merge
       |
GitOps / Terraform / Ansible authority
~~~

Agents follow the same protected branch discipline as humans. They do not get a privileged path around review.

## 7.11 Tool services over raw credentials

Prefer narrow validated interfaces:

~~~text
GET  /tools/kubernetes/pods
POST /tools/prometheus/query-template/platform-health
POST /tools/slurm/submit-offering
~~~

over giving a runtime unrestricted kubeconfig, SSH keys or raw provider credentials.

Stable tool services create a place for validation, redaction, rate limits, capability checks and audit.
