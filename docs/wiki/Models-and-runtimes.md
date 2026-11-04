# Self-hosted models, runtimes and orchestration

## Separate the four concerns

**Model**: weights and inference endpoint, for example a local vLLM-served open-weight model. **Gateway**: approved routing, credentials, budgets and reporting (for example LiteLLM). **Harness**: Hermes or an independently reviewed runtime, with its own native agent loop. **Control plane**: ACP's durable identity, policy, conversations, approvals and task ledger. No one of these subsystems replaces the others.

## Routing principles

Route by task requirements (latency, context, tool use, code quality, cost, privacy, hardware) and actual available inventory. A fast answer should not consume an H200 merely because it exists. Preserve model ID/revision, runtime, inference route, relevant parameters, task/run IDs, duration and approval evidence. A “deep reasoning” color/status should reflect observed work, not a manually selected fictional state.

Provider keys are optional for a **self-hosted** supported route. A local model is not a self-hosted copy of a closed OpenAI/Claude service or an entitlement to their proprietary weights. Never silently fall back from private inference to a remote paid provider without consent.

## Agent execution limits

Hermes is the first runtime adapter; Paperclip multi-agent pilots and other harnesses require an explicit sandbox, identity isolation, budgets, timeouts, cancellation, audit trails and human approval for mutations. ACP does not become a second Kubernetes/Slurm scheduler. Run code through typed, constrained resources; never hand unbounded cluster-admin tokens to a prompted model.

## Test before enabling

Test denial with wrong principal, timeouts, cancelled tool calls, failed model route, excessive token budgets, loss of worker session cache, replay, worker restart and recovery. Validate a second harness using *the same canonical conversation*, not a fresh chat that merely resembles it.

References: [model routing design](https://github.com/nyameko/agent-control-plane/blob/main/docs/06-model-and-compute-routing.md), [harness sandbox model](https://github.com/nyameko/agent-control-plane/blob/main/docs/07-runtimes-harnesses-and-sandboxes.md), [Paperclip pilot](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4-PAPERCLIP-ENGINEERING-PILOT.md).