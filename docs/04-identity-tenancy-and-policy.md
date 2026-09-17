# 4. Identity, tenancy and policy

## 4.1 Identity source

`quantum-platform` remains authoritative for human identity, email verification, MFA, passkeys,
research programmes and programme roles. The control plane stores an opaque external `subject`
reference and a snapshot of the authorisation context used for a task; it does not validate user
passwords or duplicate Django's account lifecycle.

The initial subject can be `django:user:<id>`. Before third-party federation, add an immutable UUID
or OIDC-compatible `sub` to `quantum-platform`; mutable email addresses must never be primary keys.

Service principals use a separate namespace, for example:

```text
service:telegram-adapter
service:discord-adapter
service:research-observer
agent:infra-orchestrator:<instance-id>
```

## 4.2 Tenant model

A tenant is an isolation and policy boundary, not only a billing label. Initial tenant forms are:

- Nyameko personal laboratory;
- a research programme;
- a CHPC or SCC teaching cohort;
- a future UY activation, club or special-interest group;
- a platform/infrastructure operations tenant.

A person may belong to several tenants. Every conversation, memory, task, artifact and channel
binding carries one tenant. Cross-tenant research collaboration is an explicit share/grant, not a
query that happens to find both parties.

## 4.3 Agent principals

An agent instance receives:

- one tenant and optional user owner;
- an immutable agent-definition and policy digest;
- a capability set;
- a model-pool allowlist;
- an execution-class allowlist;
- secret references it may request but never read into context;
- storage scopes;
- a maximum lifetime and concurrency budget.

Subagents receive equal or narrower scopes. Delegation never amplifies authority.

## 4.4 Capability model

Capabilities are verbs over narrowly defined resources:

```text
repository.read:infra-hpc-qc-k8s
prometheus.query:approved-recording-rules
slurm.submit:partition=a100,account=programme-42
artifact.write:tenant=programme-42
git.push:repo=quantum-workflows,branch=agent/*
```

Avoid coarse permissions such as `shell`, `admin` or `cluster`. A specialist may be able to query
selected Kubernetes resources without possessing a kubeconfig, because a tool service executes a
validated query on its behalf.

## 4.5 Policy decision

Policy combines:

- subject and tenant role;
- agent principal and delegation ancestry;
- requested capability and resource selector;
- sensitivity and data residency;
- input channel;
- model/runtime trust level;
- environment (`dev`, `stag`, `prod`);
- exact plan digest and approval state;
- time, quota and incident state.

Policy is enforced before planning, before every tool call, before secret resolution and before
execution. The agent's own statement that a call is safe is not policy evidence.

## 4.6 Approval contract

An approval binds:

- task and plan digest;
- actor and tenant;
- capability and concrete resource selectors;
- human-readable diff/command/impact;
- validation evidence;
- expiry and maximum uses;
- approver identity and strong-authentication level;
- outcome and execution result.

If the plan changes, approval is invalid. Telegram and Discord may notify and link to an approval;
high-risk approval occurs in `quantum-platform` with MFA/passkey re-authentication.

## 4.7 Administrative oversight

Platform administrators may inspect system-wide metadata and policy outcomes. Access to message
content and research artifacts should still be purpose-bound and audited. `is_superuser` must not
silently turn every personal research conversation into routine administrative reading.

Emergency access is a separate break-glass workflow with strong authentication, a reason, short
expiry, notification and retrospective review.
