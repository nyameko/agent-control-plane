# 3. Repository boundaries

## 3.1 Existing repository findings

The live repositories already contain a strong separation to preserve:

- `infra-hpc-qc-k8s` treats Terraform, Ansible, kubeadm/Cilium, Argo CD, Slurm,
  Prometheus/Grafana and the edge security services as independently authoritative layers. It also
  contains an isolated `hermes_orchestrator` Ansible role and detailed Hermes federation,
  multi-tenancy, harness and research-intelligence tutorials.
- `quantum-platform` has a Django/PostgreSQL identity and research-programme model, an Astro user
  portal, same-origin browser authentication, MFA/passkey foundations and audit events. Its
  production manifests correctly live in the infrastructure repository.
- `quantum-workflows` has an explicit prepare/execute/postprocess/persist lifecycle, Slurm/QRMI
  path, immutable runner model and structured scientific result/provenance contract.
- `uyuyu.africa` describes a distributed activation network in which participants become mentors,
  organisers and founders. That calls for programme/community agents with intentionally narrower
  data scopes than platform administrators.
- `chpc-tech-eval/scc` is a teaching and assessment corpus, not an operational data source. A tutor
  may retrieve it, but competition integrity and the mentor hands-off principle must remain policy.
- `.spacemacs.d` already has a private `my-gptel` layer pointing at a local Hermes-compatible
  endpoint. That is the natural advanced-user cockpit and should become a client, not absorb the
  control plane.

## 3.2 Ownership matrix

| Concern | Canonical owner | Integration artifact |
| --- | --- | --- |
| VM, network, security group, Cinder volume | `infra-hpc-qc-k8s` | Terraform modules/variables |
| host packages and isolated Hermes VM | `infra-hpc-qc-k8s` | Ansible role/playbook |
| production Deployments, Services, PVCs, NetworkPolicies | `infra-hpc-qc-k8s` | Argo CD/Kustomize resources |
| service image and application API | `agent-control-plane` | OCI image + OpenAPI/contracts |
| person, login, MFA, programme membership | `quantum-platform` | delegated identity token / API |
| chat component and Jupyter launch UX | `quantum-platform` | Astro/Jupyter client of control-plane API |
| canonical agent conversations and runs | `agent-control-plane` | PostgreSQL schema/API |
| scientific workflow implementation | `quantum-workflows` | versioned runner + workflow manifest |
| workflow catalogue, launch and result UX | `quantum-platform` | references immutable workflow version |
| physical HPC/QPU scheduling | Slurm + QRMI/QDMI/provider adapters | signed execution request/job ID |
| UY public content and activation philosophy | `uyuyu.africa` | read-only content integration |
| SCC curriculum and assessment materials | `chpc-tech-eval/scc` | read-only tutor corpus |
| Emacs UI/presets/key bindings | `.spacemacs.d` | gptel backend/presets |

## 3.3 Required changes by repository

### `agent-control-plane`

Own the portable task/run/event contracts, routing policies, agent catalog, runtime adapters,
conversation/memory APIs, approvals, audit and service image.

### `infra-hpc-qc-k8s`

Add production deployment, Cinder claims, network policies, sealed static service secrets,
database provisioning, ingress, ServiceMonitors, model-serving pools, sandbox-broker infrastructure
and least-privileged execution adapters. Pin immutable image digests.

### `quantum-platform`

Add a stable external subject identifier, delegated-token endpoint, agent preferences/retention
settings, conversation UI, approval UI, channel-linking UI, Jupyter chat extension configuration and
links between agent tasks, platform jobs and workflow results.

Do not copy all control-plane tables into the current `portal` Django app. The platform owns the
human identity and presents the UX; the control plane owns agent execution records.

### `quantum-workflows`

Keep scientific code independent of agent frameworks. Add a machine-readable workflow capability
descriptor and accept a platform/control-plane correlation ID. Preserve the existing result
manifest as the scientific record and return its URI/digest to the control plane.

### `.spacemacs.d`

Replace the hard-coded localhost-only Hermes definition with backends/presets for direct inference
and the authenticated control-plane/Hermes endpoint. Keep credentials in `auth-source`.

### `uyuyu.africa` and SCC

Initially integrate only as public/read-only knowledge sources with provenance. Later add separate
UY tenants/programmes and tutor policies; do not grant community or student agents infrastructure
administration by inheritance.

## 3.4 Cross-repository change example

An intelligent request to add an IQM workflow can become a coordinated change set:

```text
quantum-workflows
└── provider-specific runner, tests and result schema

quantum-platform
└── backend catalogue/credential UX and result presentation

infra-hpc-qc-k8s
└── QRMI/QDMI adapter, secrets path, runner digest and observability

agent-control-plane
└── capability, agent skill, routing policy and evaluation scenario
```

The control plane may coordinate branches and tests, but each repository retains its review,
CI and merge authority.
