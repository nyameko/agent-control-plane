# 4. Identity, tenancy and policy

## 4.1 Human identity authority

Quantum Platform remains authoritative for human identity, authentication, MFA/passkeys, person/profile data, research programmes and programme roles.

Agent Control Plane never validates user passwords and never invents a parallel account lifecycle.

Each participating user has an immutable Quantum Platform `AgentPrincipal` UUID. ACP consumes that UUID as its stable external subject:

~~~text
urn:quantum-platform:user:<AgentPrincipal UUID>
~~~

That subject is the durable owner reference for personal agent state.

## 4.2 AgentPrincipal is not POSIX identity

Do not derive ACP identity from UID/GID.

~~~text
Quantum Platform user
        |
        +-- AgentPrincipal UUID  -> application identity / ACP owner
        |
        +-- POSIX UID/GID        -> operating-system / scheduler identity
        +-- SSH keys
        +-- WireGuard identity
        +-- programme memberships
~~~

POSIX UID/GID may be deterministic and never reused within the platform, but it exists to make Unix files, SSH and scheduler processes work. It is an attribute linked to the principal, not the primary key of projects, conversations, memory or skills.

This separation allows future federation, multiple POSIX domains, username changes and non-POSIX clients without changing ownership of ACP state.

## 4.3 Delegated assertions

Quantum Platform issues short-lived signed assertions to ACP. Browser clients do not receive the platform signing key or ACP database credentials.

Scopes remain narrow and purpose-specific. For example:

~~~text
admin:diagnostics
agent:personal
agent:conversation:read
agent:conversation:write
agent:run:read
~~~

The exact scope vocabulary may evolve, but administrative and personal-agent authority must remain distinct.

## 4.4 Tenant and programme boundaries

A tenant is an isolation and policy boundary, not merely a billing label.

Potential forms include:

- a personal laboratory;
- a research programme;
- a teaching cohort;
- a CHPC/NICIS institutional environment;
- a UY activation/community programme;
- a platform operations tenant.

A person may belong to multiple tenants/programmes. Every durable ACP object carries an explicit owner/scope.

Cross-tenant collaboration requires an explicit share/grant. Retrieval must never cross boundaries simply because two users mention related work.

## 4.5 Personal-state isolation

Personal projects, conversations, messages and future memory are protected by both:

- tenant context; and
- subject ownership.

The database should enforce that boundary with RLS where practical so an application query bug does not automatically become a cross-user data breach.

Administrative operational records may use different visibility rules, but those rules must not silently broaden access to private research conversations.

## 4.6 Service and agent principals

Non-human principals use separate namespaces, for example:

~~~text
service:telegram-adapter
service:discord-adapter
service:model-gateway
service:execution-broker
agent:infra-orchestrator:<instance>
agent:security-specialist:<instance>
~~~

A service principal has explicitly declared capabilities and cannot impersonate a user merely because it processes that user's request.

## 4.7 Agent authority

An agent instance receives a bounded authority envelope:

- tenant and optional user/project owner;
- immutable agent-definition/version;
- capability set;
- logical model-pool allowlist;
- execution-class allowlist;
- storage scopes;
- secret references it may request;
- egress constraints;
- time/concurrency/token/resource budgets.

Subagents receive equal or narrower authority. Delegation never amplifies privilege.

## 4.8 Capabilities

Capabilities are narrow verbs over narrow resources:

~~~text
repository.read:quantum-workflows
prometheus.query:platform-health
slurm.submit:offering=qiskit-aer-large
artifact.write:project=<uuid>
git.push:repo=agent-control-plane,branch=agent/*
~~~

Avoid ambient permissions such as unrestricted `shell`, `cluster-admin` or broad provider credentials.

Prefer validated tool services and execution contracts to passing raw credentials into a runtime.

## 4.9 Policy decision

Policy considers:

- authenticated subject;
- tenant/programme;
- agent definition and delegation ancestry;
- requested capability;
- project/conversation scope;
- sensitivity and data residency;
- input channel;
- runtime/model trust;
- environment;
- quota/budget;
- incident state;
- exact plan/approval state.

Policy is enforced outside the model before privileged operations.

## 4.10 Approvals

High-impact approval binds:

- task/run and exact plan digest;
- subject and tenant;
- capability and concrete resource selector;
- human-readable impact/diff;
- validation evidence;
- expiry and use count;
- approver identity and authentication strength.

If the executable plan changes, the approval no longer applies.

External messaging surfaces may notify users of an approval request, but privileged approval should occur on an authenticated trusted surface.

## 4.11 Administrative oversight

Administrative visibility is itself a capability.

Platform operators need system health, policy outcomes, queue/resource usage and incident tools. Access to private conversation content or research artifacts should be purpose-bound, audited and exceptional rather than an automatic consequence of administrator status.

Break-glass access requires strong authentication, reason, expiry and retrospective review.
