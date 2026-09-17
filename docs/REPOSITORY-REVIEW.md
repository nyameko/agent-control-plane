# Repository review

Review date: 2026-09-17

This architecture was developed against the following public repository snapshots:

| Repository | Reviewed commit | Relevant findings |
| --- | --- | --- |
| `nyameko/infra-hpc-qc-k8s` | `9c552ea` | explicit authoritative layers; Argo CD production ownership; isolated Hermes VM role; Cinder, PostgreSQL, Slurm and agent-fabric tutorial direction |
| `nyameko/quantum-platform` | `56583da` | Astro + Django/DRF + allauth; `Person`, programmes/memberships, PI approval, audit and public-key models; same-origin session architecture |
| `nyameko/quantum-workflows` | `c2d4790` | clean three-repository ownership boundary; four-stage workflow contract; Slurm/QRMI path; redacted immutable result manifests |
| `nyameko/uyuyu.africa` | `68787fc` | distributed activation/mentor network; openness, capability-building and community reuse |
| `nyameko/.spacemacs.d` | `2151edd` | private gptel layer already targets a Hermes-compatible endpoint; natural advanced-user client |
| `chpc-tech-eval/scc` | `0d585e4` | teaching/tutorial corpus; progression from OpenStack/Linux to monitoring, automation, Slurm and quantum demonstrations |

## Findings carried forward

### 1. A fourth sibling repository is justified

Putting cross-project orchestration inside `infra-hpc-qc-k8s` would mix application contracts with
infrastructure desired state. Putting it in `quantum-platform` would couple the user portal to one
agent runtime. Putting it in `quantum-workflows` would contaminate reproducible scientific code
with operational agents. A sibling control plane is the clean seam.

### 2. Existing Hermes documentation is ahead of deployment

The infrastructure repository already describes persistent Hermes profiles, Cinder-backed state,
multi-tenant agents, Discord/Telegram routing, specialist orchestrators, harness separation and
research intelligence. The current Ansible `hermes_orchestrator` role is intentionally a minimal
host/security-policy foundation. This repository converts the broader design into portable
contracts and an incremental deployment path rather than pretending all components already run.

### 3. The identity model is usable but needs a stable external subject

Django is already authoritative for user, MFA, PI and programme membership. The agent control
plane should reference it, not duplicate it. The current integer user ID can bootstrap integration;
an immutable subject UUID/OIDC `sub` should be added before wider federation.

### 4. Existing `AuditEvent` is not enough for agent lineage

`quantum-platform` correctly records approval-sensitive domain events. Agent execution additionally
needs task/run/delegation/model/tool/approval/job lineage. Those records belong in the control-plane
database and can be summarised/linkable from the portal audit view.

### 5. Scientific and agent provenance must remain distinct

`quantum-workflows` already emits source/software/resource/circuit/result manifests. The agent
record should point to those manifests rather than replace them with a chat transcript or copy them
into agent memory.

### 6. Spacemacs needs a server-side abstraction, not many physical endpoints

The current gptel layer proves the interaction model. Its hard-coded local Hermes/model values
should evolve into logical presets and authenticated endpoints. Physical A100/H200/model changes
then happen behind the model gateway and control-plane router.

### 7. UY and SCC need distinct educational policy

UY's participant-to-mentor flywheel makes tutoring, translation, collaboration and reusable skills
high-value future agents. SCC assessment and mentor hands-off rules mean those agents also need
course/cohort policy: teach and diagnose without silently completing assessed work or controlling
student infrastructure.

## Known source inconsistency

Some current `infra-hpc-qc-k8s` prose still describes “Hermes/Heretic” as orchestration/execution.
Current upstream Heretic is a model-weight modification project, not a Hermes memory or execution
harness. This repository therefore treats Heretic as optional model engineering and keeps runtime
orchestration with Hermes/adapters/sandboxes.
