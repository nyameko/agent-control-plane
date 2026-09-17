# 7. Runtimes, harnesses and sandboxes

## 7.1 Four different things

| Layer | Examples | Responsibility |
| --- | --- | --- |
| model | Qwen, DeepSeek, Llama, Mistral | generate/reason |
| inference runtime | Ollama, llama.cpp, vLLM | serve model weights |
| agent runtime/harness | Hermes, DeepSeek Harness, CLI agents | tool loop, sessions, delegation, context |
| execution environment | OpenStack VM, container, Kubernetes Job, Slurm allocation | run code and commands |

An agent runtime can be a small CPU service using a model served remotely on H200 and tools running
in a third environment.

## 7.2 Hermes-first integration

Hermes is the initial full runtime because its current programmatic surfaces already cover:

- OpenAI-compatible chat/responses;
- stateful runs and SSE lifecycle events;
- stop, steer and approval operations;
- persistent sessions, memory and skills;
- tool use and subagent delegation;
- profiles and messaging gateways;
- multiple execution backends.

The adapter stores a mapping:

```text
control-plane task/run/conversation
               ↕
Hermes run/session/profile
```

Hermes never becomes the source of platform identity or global policy. The control plane validates
each privileged tool request even if Hermes also has a local approval feature.

## 7.3 Adapter contract

Every runtime adapter should implement:

- capability discovery;
- create/resume/branch/stop session;
- submit input and stream normalised events;
- tool/approval request translation;
- model-pool selection where supported;
- artifact attachment;
- usage/result/error reporting;
- health and version reporting.

Runtime-specific payloads live below `extensions`; portable clients consume the V1 event contract.

## 7.4 DeepSeek Harness

DeepSeek Harness is promising for plugin-driven experimental coding/research workflows. Its current
project explicitly labels itself a developer preview with compatibility-breaking changes expected.
Treat it as an experimental runtime adapter or specialised executor. Do not make production state
or security policy depend on its internal plugin interfaces yet.

## 7.5 Herder

Herder is a local job supervisor for CLI agents with queueing, roles, fallbacks, concurrency and
result collection. It may be useful as:

- a workstation development adapter;
- a remote pool of CLI coding workers;
- an experiment in provider fallback and agent benchmarking.

It does not replace the control-plane database, Kubernetes, OpenStack sandbox broker or Slurm. Do
not nest independent retry/queue systems without one clear owner for task state.

## 7.6 Heretic correction

Heretic is a model-weight modification/abliteration project. It belongs under model engineering and
controlled evaluation, not under agent memory, skills or orchestration. Any modified model must be
registered as a distinct artifact with licence, provenance, evaluation and safety metadata.

## 7.7 Sandbox broker

Never run arbitrary agent-generated commands in the API or Hermes control-plane container. A
sandbox request includes:

- task/run/tenant/subject IDs;
- immutable source repository and commit;
- writable worktree/branch destination;
- base image digest;
- CPU, memory, GPU, wall-clock and disk limits;
- egress/DNS policy;
- allowed secret *references* and injection destinations;
- allowed command/tool family;
- artifact/output contract;
- lease, heartbeat and cleanup policy.

The broker creates an isolated OpenStack VM, container, Kubernetes Job or Slurm allocation and
returns an opaque execution ID. Workers do not receive control-plane database credentials.

## 7.8 Repository modification workflow

```text
read-only clone at approved commit
        ↓
isolated worktree/branch
        ↓
agent changes + tests + evidence
        ↓
patch / branch proposal
        ↓
human and CI review
        ↓
merge by authorised Git identity
        ↓
Argo CD / Terraform / Ansible authority
```

The first production capability should stop at patch generation. Later, a dedicated Git service
principal may push only `agent/*` branches after plan approval. It still cannot merge protected
branches.

## 7.9 Tool services over raw credentials

Prefer a narrow service such as:

```text
GET /tools/kubernetes/pods?namespace=monitoring
POST /tools/slurm/validate
POST /tools/prometheus/query-template/platform-health
```

over giving each agent a kubeconfig, SSH key or unrestricted Prometheus query. This creates stable
validation, redaction, rate limiting and audit boundaries.
