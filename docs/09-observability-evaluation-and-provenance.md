# 9. Observability, evaluation and provenance

## 9.1 Three records

Keep these separate:

1. **Operational telemetry** — service health, latency, errors, queues, resource use.
2. **Security/audit record** — who requested, delegated, approved, accessed or executed what.
3. **Scientific provenance** — workflow inputs, software, hardware/QPU, methods and result digests.

Prometheus is suited to bounded aggregate metrics. PostgreSQL/append-only audit storage records
security events. `quantum-workflows` manifests remain the scientific record.

## 9.2 Metrics

Suggested bounded labels: tenant class, agent type, model pool, runtime, execution class, status,
approval outcome and error class. Do not label metrics with user, conversation, task, run, provider
job or experiment IDs.

Measure:

- request/first-token/completion latency;
- task and delegation success/failure/cancellation;
- tool-call and sandbox failure rates;
- approval queue age and outcome;
- model tokens, GPU seconds and queue delay;
- sandbox CPU/GPU/QPU resource seconds;
- routing fallback and policy-denial counts;
- retrieval relevance and memory-correction rates;
- channel delivery latency/failure;
- cost/energy proxies by tenant and pool.

## 9.3 Distributed traces and correlation

Propagate an opaque correlation ID across client, control plane, Hermes, model gateway, sandbox and
Slurm/QRMI. Store task/run/job mappings in the database. Trace attributes must not include prompts,
secrets or raw research data.

## 9.4 Agent evaluations

An agent definition is not ready because its prompt sounds good. Evaluate it against versioned
scenarios:

- correct repository and specialist selection;
- refusal to cross tenant/capability boundaries;
- prompt-injection resistance in logs, papers and chat;
- patch correctness and test evidence;
- appropriate model/compute selection;
- citation/provenance accuracy;
- recovery from tool/model failure;
- calibrated uncertainty and escalation;
- resource/time efficiency.

Maintain separate development, staging and production evaluation data. Never run destructive
production acceptance tests to prove an agent knows not to be destructive.

## 9.5 Routing evaluation

Compare logical routes on:

- success against domain-specific acceptance tests;
- latency distribution and queue time;
- tokens and compute consumed;
- human correction/rejection rate;
- tool iterations and failed calls;
- sensitivity/policy violations (target: zero).

The routing model may optimise measured quality/cost only within hard policy constraints.

## 9.6 Workflow provenance link

When an agent launches `quantum-workflows`, the control plane stores the task/run and platform job
references. The scientific result stores its own workflow manifest. Each record points to the
other by URI/digest without duplicating or rewriting the scientific provenance.

## 9.7 Audit durability

Audit events are append-only at the application boundary and exported to an independently
protected store/observability pipeline. Agent runtimes cannot delete or rewrite them. Sensitive
payloads are represented by typed summaries and artifact digests rather than raw secrets or full
prompts.
