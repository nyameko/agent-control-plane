# 6. Model and compute routing

## 6.1 Two independent placement decisions

Every non-trivial task may need two routes:

1. **Inference route:** which model and serving runtime produce reasoning/tool calls?
2. **Execution route:** where do tools, builds, tests or scientific jobs execute?

Example:

```text
Hermes agent:          small Kubernetes pod
inference:             large model served by vLLM on H200
repository sandbox:    ephemeral 64-vCPU OpenStack VM
scientific stage:      Slurm A100/H200 allocation
QPU stage:             Slurm + QRMI/QDMI/provider adapter
```

GPU inference capacity and user workload capacity should have separate quotas and telemetry even
when they share hardware.

## 6.2 Logical model pools

Clients and agents ask for service classes such as:

- `general-fast`;
- `general-private`;
- `code-interactive`;
- `reasoning-deep`;
- `reasoning-private`;
- `embedding-private`.

The model gateway maps them to a reviewed model/runtime deployment. Model names and hardware may
change without rewriting gptel presets or agent definitions.

Routing inputs include:

- task/domain and required tool-use capability;
- quality target and latency deadline;
- context length and expected output;
- sensitivity, data residency and external-provider permission;
- current queue, health and available KV-cache capacity;
- measured performance on relevant evaluations;
- energy/token/compute budget and tenant quota.

The router must record the chosen pool, resolved model/runtime, policy constraints, fallbacks and
reason codes.

## 6.3 Serving runtime roles

| Runtime | Recommended role |
| --- | --- |
| Ollama | workstation, development, rapid model trials, low-concurrency services |
| llama.cpp | CPU/edge deployments, quantised models, efficient specialised serving |
| vLLM | production A100/H200 throughput, batching and multi-GPU serving |
| external API | explicit opt-in fallback or evaluation where policy allows |

A gateway such as LiteLLM can provide one OpenAI-compatible endpoint, authentication, budgets,
fallbacks and usage accounting. It is a model gateway, not the task orchestrator or policy source.

## 6.4 Logical execution classes

Agents request capability/resource envelopes, never hostnames:

| Class | Use |
| --- | --- |
| `none` | conversation/reasoning only |
| `sandbox-cpu-standard` | isolated repo analysis, lint, small tests |
| `sandbox-cpu-large` | compilation, larger CPU tests, local emulation |
| `kubernetes-job` | bounded asynchronous service work |
| `slurm-a100` | single-GPU development/evaluation |
| `slurm-h200` | large-model or large-memory simulation |
| `slurm-multinode` | MPI/distributed workloads |
| `slurm-qpu-*` | scheduler-mediated QPU job |

The execution broker translates the envelope to an OpenStack request, Kubernetes Job or `sbatch`
specification. The target scheduler makes physical placement decisions.

## 6.5 A100, H200 and CPU policy

- 32/64-vCPU VMs run the control plane, CPU sandboxes, static analysis, build/test workers and
  modest models where practical.
- A100 serves interactive coding/general pools, embeddings, reranking, evaluations and medium
  simulation.
- H200 serves large/deep models, long context, high concurrency and high-memory simulation.
- Slurm owns large or multi-node scientific execution; Kubernetes owns durable services and
  bounded service jobs.
- The H200 is not the default simply because it is the most powerful resource. Measured quality
  gain must justify queue, energy and opportunity cost.

## 6.6 Routing evolution

### V0.1 — deterministic policy

The code in this repository produces an explainable logical plan from explicit request fields.

### V0.2 — telemetry-aware selection

Resolve healthy deployments using queue depth, latency, context capacity and quotas.

### V0.3 — evaluation-aware routing

Use model/harness success rates by task family, but keep hard policy constraints outside the model.

### V0.4 — learned ranking with guardrails

A learned router may rank candidates. It cannot expand the candidate set beyond policy or directly
name physical production nodes.

## 6.7 Scheduling anti-patterns

- do not let an LLM reimplement Slurm priority/backfill;
- do not reserve H200s while waiting in a public QPU queue;
- do not place user scientific jobs in the model-serving deployment;
- do not use Prometheus high-cardinality labels for task/run IDs;
- do not silently fall back from a private model to an external API;
- do not report “best model” without task-specific evaluation evidence.
