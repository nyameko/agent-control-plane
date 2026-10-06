# 3. Repository and authority boundaries

## 3.1 Core repository family

The four core repositories intentionally separate infrastructure, product, agent coordination and scientific execution.

| Repository | Canonical responsibility |
| --- | --- |
| `infra-hpc-qc-k8s` | OpenStack, hosts, networking, Kubernetes substrate, Cinder, security controls, observability, GitOps deployment and Slurm infrastructure |
| `quantum-platform` | Human identity, AgentPrincipal, programmes, entitlements and researcher-facing product experience |
| `agent-control-plane` | Canonical agent context, task/run history, runtime mappings, policy, approvals and portable agent orchestration contracts |
| `quantum-workflows` | Reproducible scientific workflows, runners, provider integration and scientific result provenance |

This separation is foundational.

## 3.2 Ownership matrix

| Concern | Canonical owner | ACP role |
| --- | --- | --- |
| Human login/MFA/passkeys | quantum-platform | consume delegated identity |
| AgentPrincipal UUID | quantum-platform | stable external subject |
| POSIX UID/GID | quantum-platform identity/provisioning | linked execution attribute |
| Project/conversation/message state | agent-control-plane | canonical owner |
| Memory and skill bindings | agent-control-plane | canonical owner |
| Runtime-native session/cache | runtime | store correlation only |
| Agent task/run/event/audit history | agent-control-plane | canonical owner |
| VM/network/Cinder/Kubernetes resources | infra-hpc-qc-k8s | request bounded execution/deployment changes |
| Slurm scheduling state | Slurm | keep external job references/observations |
| Workflow scientific provenance | quantum-workflows | correlate task/run with workflow manifest |
| User-facing chat/project UX | quantum-platform | render ACP state |
| Git source/policies/shared skills | Git repositories | reference immutable versions |
| Large artifacts | project/object/artifact storage | store metadata/digests/references |

## 3.3 Agent Control Plane

ACP owns:

- project/conversation/message APIs;
- memory and skill contracts;
- task/run/event lineage;
- runtime adapter contracts;
- runtime/profile/session mappings;
- capability/policy decisions;
- approvals;
- model/execution routing metadata;
- artifact and scheduler references;
- service images and application migrations.

ACP does not own user passwords, physical scheduling or scientific result truth.

## 3.4 Quantum Platform

Quantum Platform owns:

- user authentication;
- AgentPrincipal UUID;
- person/profile data;
- programme membership and entitlements;
- POSIX identity allocation/provisioning policy;
- user-facing account/project/chat/workbench/run UX;
- short-lived delegated assertions to ACP.

Quantum Platform is a client and identity authority. It does not duplicate ACP's canonical conversation/memory database.

## 3.5 Infrastructure repository

`infra-hpc-qc-k8s` owns deployment/runtime infrastructure:

- Terraform/OpenStack;
- Ansible/host roles;
- Kubernetes/Cilium/Cinder;
- Argo CD desired state;
- ACP PostgreSQL/worker/API deployment resources;
- NetworkPolicy and secret plumbing;
- Prometheus/Grafana/Wazuh/Suricata;
- Slurm;
- later model-serving pools and sandbox infrastructure.

Application source and schema semantics remain in their application repositories.

## 3.6 Quantum Workflows

`quantum-workflows` remains independent of agent frameworks.

It should accept portable execution/correlation metadata and return durable scientific provenance/results.

Agents may propose or submit workflows through authorised platform contracts, but ACP does not rewrite the scientific record.

## 3.7 Editors, Jupyter and terminal clients

JupyterLab, gptel/Spacemacs and SSH/TUI surfaces are clients of ACP.

They do not own separate canonical chat histories.

A client may cache local UI/session data, but every durable project/conversation identifier comes from ACP.

## 3.8 External programmes and teaching repositories

UY, SCC/AICE/QCC and related education/community systems can later consume ACP through narrower tenant/programme scopes.

They do not inherit infrastructure-administrator authority.

Teaching content remains content; assessment policy remains policy.

## 3.9 Cross-repository change pattern

A future new IQM/Pasqal/D-Wave integration may require coordinated changes:

~~~text
quantum-workflows
└── workflow/provider runner + scientific provenance

quantum-platform
└── entitlement/credential UX + offering/result presentation

infra-hpc-qc-k8s
└── deployment/secrets/network/scheduler integration

agent-control-plane
└── capabilities/runtime/tool/routing/evaluation contracts
~~~

Each repository keeps independent review, CI, branch protection and release authority.

ACP may coordinate work, but it does not become a privileged merge authority.
