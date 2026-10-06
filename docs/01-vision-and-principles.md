# 1. Vision, objectives and guiding principles

## 1.1 Vision

Agent Control Plane is the durable coordination layer for a self-hosted virtual research and engineering organisation whose compute fabric ranges from a researcher's workstation to Kubernetes, Slurm, accelerated GPU systems and eventually QPUs.

The project is not primarily about building a better chatbot.

It is about preserving **research continuity and authority** while intelligence and compute remain heterogeneous and replaceable.

A researcher should be able to:

- begin a project in Quantum Platform;
- continue the same conversation in Jupyter;
- attach from SSH or an editor;
- use a different agent runtime for a coding task;
- move inference from a local model to an A100/H200 service;
- submit heavy work to Slurm;
- submit quantum work through an authorised provider path;
- return later and still have the same project, context, provenance and policy boundary.

That continuity is the product.

## 1.2 The problem ACP solves

Without a control plane, state tends to become trapped in the component that happened to create it:

~~~text
browser chat history
Hermes profile database
editor buffer
notebook filesystem
coding-agent session
model-provider conversation ID
shell history
~~~

Those are useful local representations, but they are poor foundations for a long-lived multi-user research platform.

ACP separates durable platform context from replaceable execution machinery.

## 1.3 Objectives

ACP should make the following properties true.

### Durable continuity

Projects, conversations, memory, skills and run history survive ordinary client, Pod, process and runtime replacement.

### Runtime independence

Hermes is the first runtime adapter, not the permanent data model. Other runtimes and harnesses can be introduced without migrating the user's canonical history.

### Model independence

Agent definitions refer to logical model capabilities. The platform may change weights, serving runtimes or providers without changing user/project identity.

### Execution independence

A conversation can request bounded work without knowing which physical node performs it. Kubernetes, OpenStack, Slurm and QPU providers remain authoritative schedulers.

### Explicit authority

Humans, agents, tools, runtimes and schedulers each have explicit scopes. Delegation never silently amplifies privilege.

### Reproducibility

Operational decisions, code changes and scientific results retain enough evidence to reconstruct what happened and why.

### Portability and openness

The architecture favours open interfaces, self-hostable components and open-weight models while avoiding assumptions that prevent authorised external integrations.

### Educational value

The platform should expose its architecture, failures, acceptance tests and trade-offs clearly enough to teach students and researchers how heterogeneous research infrastructure actually works.

## 1.4 Guiding principles

### One canonical owner per state class

A state item may have replicas, caches and runtime-local forms, but one system must be authoritative.

Examples:

~~~text
human identity            -> Quantum Platform
agent conversation        -> ACP
agent memory              -> ACP
Hermes runtime cache      -> Hermes profile
scientific result         -> quantum-workflows
Slurm job state           -> Slurm
Git source                -> Git repository
~~~

### Context is more durable than intelligence

Models improve rapidly. Agent frameworks change rapidly. User projects should not have to.

ACP therefore treats model and runtime selection as execution metadata rather than the identity of a conversation.

### Policy is deterministic at the trust boundary

An LLM may recommend an action. It may not decide that it has permission to perform the action.

Identity, tenancy, capability, egress, secret, approval and scheduler policy are enforced outside model reasoning.

### The smallest reliable vertical slice wins

Avoid adding a new framework merely because it exists. Add a component when it solves a measured problem and can pass a failure/recovery test.

This principle directly governs M4a.

### Durable does not mean permanent

Users need retention, archive, export, correction and deletion semantics. Audit or research-retention obligations should be explicit exceptions rather than accidental immortality.

### Runtime-native features are accelerators, not authorities

If Letta, Hermes, LangGraph, Agent Framework or another runtime has memory or checkpointing, ACP may exploit it. The portable platform record remains independent.

### Strong boundaries make experimentation easier

A strict adapter boundary makes it safer to experiment with new models, model modifications, harnesses and orchestration strategies because replacing them does not threaten canonical state.

### Human sovereignty for high-impact actions

The user owns the objective. High-impact mutations require explicit capability and approval. Autonomy is expanded only after reversible lower-risk paths have earned trust.

### Evidence before confidence

Useful output links to the evidence that produced it: tool calls, tests, model/runtime revisions, workflow manifests, scheduler IDs, artifacts and unresolved uncertainty.

### Failure is part of the design

Processes die. Pods move. models become unavailable. networks partition. credentials rotate.

The architecture should make those events ordinary recovery paths, not data-loss events.

### African research capability

The platform should lower the barrier between learners, researchers and advanced heterogeneous computing resources while preserving local ownership, open skills development and the ability to operate within South African and African research infrastructure.

## 1.5 Three independent hierarchies

Do not collapse:

1. administrative authority;
2. agent delegation/orchestration;
3. physical compute scheduling.

A platform administrator can ask an infrastructure agent to investigate a problem. That does not mean the agent receives every administrator credential, and it does not mean it chooses physical Slurm placement.

## 1.6 Virtual organisation model

The long-term system can expose specialists such as:

~~~text
coordination / research organisation
├── research assistants
├── software engineering agents
├── security operations agents
├── storage/data agents
├── user-management agents
├── education/tutorial agents
├── observability agents
└── scientific workflow specialists
~~~

These are policy-scoped software principals, not personalities with implicit organisational authority.

Paperclip may later coordinate these runtimes and specialists. ACP remains the state and policy substrate underneath that coordination.

## 1.7 Non-goals

ACP does not aim to:

- replace Kubernetes, Slurm, OpenStack, Terraform or Argo CD;
- duplicate Quantum Platform's user-account lifecycle;
- absorb quantum-workflows scientific logic;
- make every model self-hosted at all costs;
- require one agent framework;
- store secrets in prompts or long-term memory;
- expose one universal shell to every agent;
- hide infrastructure decisions that need auditability;
- optimise for maximum autonomy before durability and policy are proven.

## 1.8 Engineering discipline

The project follows the wider platform governance model:

~~~text
feature/* / agent/* / student/*
             |
             v
         protected dev
             |
      integration + CI
             |
             v
       release/vX.Y.Z
             |
      freeze / staging
             |
             v
        protected main
~~~

Major platform releases follow an approximately six-month cadence: five months of active development/integration and roughly one month of release freeze, stabilisation and conformance testing.

That cadence should not prevent continuous upstream tracking and small compatible improvements between releases.
