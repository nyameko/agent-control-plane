# 6. Model and compute routing

## 6.1 Keep four decisions separate

A task may involve four independent choices:

1. which specialist/agent should work on it;
2. which runtime/harness should host that agent;
3. which model/inference service should provide reasoning;
4. where external code/scientific execution should run.

Example:

~~~text
specialist            research/coding agent
runtime               Hermes or OpenHands
inference             reasoning model served by vLLM on H200
build/test sandbox    64-vCPU OpenStack worker
scientific execution  Slurm H200 allocation
QPU stage             provider/QRMI/QDMI broker
~~~

Do not collapse these into one "agent location".

## 6.2 Logical model pools

Clients and agent definitions request capabilities rather than immutable model names.

Suggested pools:

- `fast-local`
- `general-balanced`
- `deep-reasoning`
- `coding`
- `vision`
- `long-context`
- `research`
- `restricted-local`
- `embedding-private`

The model gateway resolves a pool to a reviewed model + inference runtime + endpoint.

Changing the resolved model must not change principal/project/conversation identity.

## 6.3 Open-weight and provider flexibility

The architecture should remain compatible with changing open/open-weight families such as Qwen, DeepSeek, Mistral/Devstral, gpt-oss and future models.

The exact best model is deliberately not encoded in ACP's data model.

External providers may be allowed for explicitly authorised workloads. Private/restricted data should fail closed rather than silently route externally.

## 6.4 Inference runtimes

| Runtime | Likely role |
| --- | --- |
| Ollama | workstation/dev/small specialist services |
| llama.cpp | CPU/edge/quantised specialist serving |
| vLLM | production A100/H200 throughput and batching |
| future compatible server | allowed behind the same logical model-gateway contract |

A model gateway can provide authentication, quotas and routing. It is not the agent task authority.

## 6.5 Meta-orchestration and runtime selection

Later, Paperclip can choose among allowed specialists/harnesses.

ACP supplies the candidate set based on:

- subject/tenant;
- capability;
- privacy/sensitivity;
- task family;
- runtime health;
- model compatibility;
- budgets/quotas;
- evaluation history.

Paperclip or another orchestrator may rank/coordinate candidates but cannot expand authority beyond policy.

## 6.6 Logical execution offerings

Agents should request platform-visible logical execution offerings, not hostnames or secret partition implementation details.

Examples:

- `cpu-small`
- `qiskit-aer-large`
- `h200-accelerated`
- `sandbox-cpu-standard`
- `sandbox-cpu-large`
- `quantum-provider:<capability>`

The authoritative execution layer maps those offerings to Slurm/Kubernetes/OpenStack/provider specifics.

## 6.7 Inference versus scientific execution

Inference resources and user scientific resources need independent quotas and accounting.

A small ACP worker can:

- reason through a model hosted on H200;
- submit a CPU scientific job;
- later submit a QPU stage;

without holding all those resources simultaneously.

Do not reserve scarce GPU capacity while waiting on a remote QPU queue.

## 6.8 A100/H200 journey

After M4:

~~~text
A100 / H200 serving pools
        |
        v
logical model gateway
        |
        v
health / quotas / evaluation
        |
        v
routing reasons recorded in ACP
~~~

The most powerful accelerator is not automatically the default.

Use measured quality, context needs, latency, concurrency and cost/energy opportunity cost.

## 6.9 Routing evolution

### Deterministic

Explicit model/runtime/execution policy.

### Telemetry-aware

Health, queue depth, latency, context capacity, quotas.

### Evaluation-aware

Measured success by task family and runtime/model combination.

### Learned ranking

A learned/meta router may rank candidates, but hard privacy/capability/resource policy defines the candidate set.

## 6.10 Anti-patterns

- hard-code one model family into every agent definition;
- let an LLM choose unrestricted physical nodes;
- let Kubernetes and Slurm allocate the same GPUs independently;
- silently fall back from local/private to external inference;
- equate parameter count with task quality;
- let the meta-orchestrator become the canonical state database;
- let model-serving failures erase conversations.
