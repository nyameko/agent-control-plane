# Model, harness and client lifecycle

## Independent lifetimes

An agent runtime or harness maintains a temporary tool loop and possibly a local session cache; ACP maintains the long-lived project/conversation and task ledger. Model inference can be served through vLLM/LiteLLM or a similarly configured route, but the model must not control identity or resource grants. Slurm/Kubernetes remain the resource schedulers.

A user should be able to create a private project in Quantum Guide, attach from a permitted second client, restart a worker, change a compatible model/harness route, and still see the **same canonical messages and IDs**. A harness restoring its private session without ACP history is a failure of the architecture.

## Personal worker principles

The worker reads its input from a trusted API/queue with a scoped AgentPrincipal and task identifier; it reconstructs context from PostgreSQL rather than assuming the browser or local runtime survived. Enforce bounded run duration, cancellation, retries and a single committed final result per idempotent task. Persist tool provenance and observed errors. A model's own statement “I restarted successfully” does not demonstrate restart success.

## Destructive acceptance

Use an isolated authorized test user and a distinctive nonsecret marker. Record project/conversation IDs, send a message, end browser/Jupyter/terminal sessions, replace the worker and clear *ephemeral* runtime state (not ACP database), then retrieve the same canonical transcript. Verify wrong-user/tenant access is denied. Do not execute destructive production tests without explicit operator approval and recovery plan.

## Alternate harness evidence

An alternate provider/harness should read canonical context through the same protected contract and write back the same conversation; simply starting a second agent with a copied prompt is insufficient. Test misrouting, slow inference, cancellation, token budgets, forbidden tool calls, missing model server and persistence after runtime crash.

## Terminal boundary

The current source provides a thin `acp` client that can accept a trusted short-lived assertion on standard input. Portal-mediated terminal pairing is a **proposed** contract (ADR 0012), not a deployed login broker. Never tell users that SSH/POSIX credentials alone grant ACP access.

References: [M4 persistent agent](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4-PERSISTENT-AGENTS.md), [personal worker source](https://github.com/nyameko/agent-control-plane/blob/main/src/agent_control_plane/personal_worker.py), [runtimes and sandboxes](https://github.com/nyameko/agent-control-plane/blob/main/docs/07-runtimes-harnesses-and-sandboxes.md), [terminal ADR](https://github.com/nyameko/agent-control-plane/blob/main/docs/adr/0012-portal-mediated-terminal-authentication.md).