# 1. Vision and principles

## 1.1 From chatbot to virtual organisation

The long-term system is a self-hosted virtual engineering and research organisation. A user should
be able to ask for help from the portal, a notebook, Spacemacs, Telegram or Discord and encounter
the same identity, conversation and research context. Behind that surface, work can be delegated to
specialists with different tools, models, security scopes and compute.

The useful organisational analogy is:

```text
executive control plane
    ├── infrastructure department
    ├── research department
    ├── security operations
    ├── education/tutoring
    └── community and collaboration
```

The analogy stops at authority. Agents are software principals operating under machine-enforced
policy. They are not employees who may improvise access because a task sounds important.

## 1.2 Three forms of hierarchy

Do not collapse these hierarchies:

1. **Administrative authority** — platform administrators, PIs, programme admins, researchers,
   students and service principals.
2. **Agent delegation** — executive orchestrator, department orchestrators and specialists.
3. **Compute scheduling** — model serving pools, sandboxes, Kubernetes jobs, Slurm allocations and
   QPU brokers.

An administrative superuser may ask the executive orchestrator to investigate everything. That
does not mean every specialist inherits superuser credentials, and it does not mean the resulting
work bypasses Git review or scheduler policy.

## 1.3 The superuser control plane

Nyameko's administrative view should provide:

- cross-tenant operational visibility where policy permits;
- agent/run/task lineage and the delegation tree;
- model, token and compute utilisation;
- pending approvals and blocked actions;
- security and reliability summaries;
- the ability to stop, steer, quarantine or revoke an agent principal;
- policy and agent-definition version history.

It should not provide one shared shell with every credential loaded. Oversight is safer when it is
implemented as scoped queries and approvals rather than universal ambient access.

## 1.4 Philosophical principles

### Human sovereignty

The user owns the objective, identity, data and final high-impact decision. Automation should make
intent easier to carry out, not make human intent irrelevant.

### Evidence before confidence

An agent reports the sources, tool output, tests, resource measurements and policy decisions that
support a result. Confidence without inspectable evidence is not an operational control.

### Capability before personality

A `SOUL.md` or system prompt can shape behaviour. Security comes from capabilities, isolated
credentials, sandboxing and independent enforcement. A trustworthy personality is not an IAM
policy.

### Reversibility

Prefer proposed diffs, branches, snapshots, immutable artifacts and declarative reconciliation.
Changes should have an identified rollback before approval.

### Learning and teaching

Consistent with the existing infrastructure tutorials, UY activation model and SCC material,
failures, routing choices, acceptance tests and trade-offs are part of the educational product.

### African research capability

The system should lower the distance between a learner, a researcher and serious heterogeneous
compute. It should support modest local environments and scale to national HPC/GPU/QPU resources
without making either end a second-class path.

## 1.5 What the project is not

- not a new Kubernetes, Slurm or OpenStack scheduler;
- not a model server;
- not a replacement for `quantum-platform` identity and user experience;
- not a home for scientific algorithms that belong in `quantum-workflows`;
- not a GitOps repository for production manifests;
- not one enormous prompt containing the entire organisation;
- not a licence for unsupervised production mutation.
