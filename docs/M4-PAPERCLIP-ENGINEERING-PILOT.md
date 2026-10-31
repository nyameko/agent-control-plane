# M4 engineering-agent pilot — adopt Paperclip, do not rebuild a supervisor

Status: proposed review gate (no deployment). Linked to [ACP #8](https://github.com/nyameko/agent-control-plane/issues/8) and [M4 release #45](https://github.com/nyameko/agent-control-plane/issues/45).

## Upstream implementation to reuse

Review the current **pinned upstream SHA** at pilot design freeze; do not pull a mutable `master` image. Canonical upstream is [paperclipai/paperclip](https://github.com/paperclipai/paperclip); see its `doc/DEPLOYMENT-MODES.md`, `doc/DOCKER.md`, `doc/MCP-ACCESS-GOVERNANCE.md`, `doc/LOW-TRUST-PRESETS.md`, `doc/HERMES_GATEWAY_ONBOARDING.md`, `doc/UNTRUSTED-PR-REVIEW.md` and `doc/RUNNER-INTEGRATION-PLAYBOOK.md`.

Paperclip already provides authenticated/private instance mode, persistent agent tasks/heartbeats, `hermes_local` and `hermes_gateway` adapters, Codex/Claude tooling, MCP application/connection/catalog/profile/policy/audit, and a low-trust review preset. Reuse these. Do not create competing ACP tables for heartbeat scheduling, tool catalogs or a second issue tracker.

## Authority and isolation

- **Paperclip** owns operational orchestration/agent-company task state.
- **ACP** owns canonical Quantum Platform researcher projects, conversations, approved memory, policies, run correlations and allowed capabilities. Map Paperclip instance/company/issue/run IDs to ACP task/run references only at the integration boundary.
- **Quantum Platform** is the only authority for research-user AgentPrincipal identity; a Paperclip Board identity is not automatically a Quantum Platform researcher.
- **GitHub** remains the auditable engineering issue and PR workflow, requiring human review and protected branches.
- **LiteLLM** owns logical model/provider routing and quotas; A100/H200 vLLM expose only approved model endpoints.
- **Slurm/Axis** owns GPU scheduler reservations and execution identity. Never let Paperclip and Slurm both believe they own the same GPU.
- **Sandbox**: isolated disposable VM/container for coding agents, without production credentials, home-dir mounts, SSH agent, Docker socket or K8s service-account tokens.

## Phase 0: no credentials, no GitHub mutation, no GPU requirement

1. Obtain one immutable Paperclip release or commit and review its license/SBOM/provenance and container/base image. Pin images by OCI digest.
2. Pilot Paperclip in `authenticated/private`, private network only; persistent storage **independent** of ACP PostgreSQL. Keep all deployment on an isolated non-production VM/environment until trusted security validation.
3. Create two task-limited roles: `engineer` (branch/PR in disposable checkout) and `reviewer` (test findings and PR evidence). Research specialist third only after first cycle succeeds.
4. First MCP exercise: upstream's **safe read-only Todo/KV fixture**. Require allow-read, deny-write, auditable decision and rejection of unauthorized calls before any live provider connection.
5. Use `low_trust_review` policy for GitHub issues/PR content. Treat external issues, diff, markdown, build logs and tool output as untrusted instructions.
6. Verify restart persistence: process killed and restarted; task identity and audit survive. Verify cancellation, pause, no infinite heartbeat loop and bounded retries.

## Phase 1: one carefully authorized GitHub issue

- Select **one** harmless approved issue, e.g. Quantum Platform #61 run-status UX test plan or its smallest isolated fix.
- Grant repository-scoped token with minimal permissions; read first, and add PR branch-write permission only after proving sandbox isolation and audit. **Never provide an agent access to `main`, `dev`, production repo secrets or merge/deploy authority.**
- Prefer GitHub App installation-scoped tokens or fine-grained credentials brokered to an isolated executor. Check real token privileges by negative tests; do not rely on a prompt saying 'do not merge'.
- Agent may create a draft PR from `agent/*` with CI receipts; reviewer checks regression, threat model, changed files and evidence. Human chooses merge.
- Record a single-task duration/iteration/token budget, max concurrency 1 initially, max retries 2, explicit kill/cancel path, and approval escalation.
- Fail closed if model endpoint or MCP gateway fails; never fall back to an unapproved external endpoint.
- No automatic code execution on untrusted input with host mounts or production credential exposure.

## Phase 2: inference and H200

- Reuse the existing A100 `research-general` route for initial pilot *only if* model quality and tool-call behavior pass smoke tests; latency and coding quality are measured.
- Evaluate logical `research-fast`, `research-reasoning`, `research-literature`, `engineering-code` routing with model/backend revision, latency, tokens/cost, fallback and policy.
- H200 `xd670` must not receive ACP PostgreSQL or Paperclip's authoritative controller. Place long-lived model serving on approved, dedicated GPUs only under infra [#82](https://github.com/nyameko/infra-hpc-qc-k8s/issues/82) and [#124](https://github.com/nyameko/infra-hpc-qc-k8s/issues/124), using audited outbound TLS/WSS broker and no overlapping Slurm GPU allocation.
- Approval required for firewalls, outbound endpoints, Kubernetes/Slurm reconfiguration and model weight downloads.
- A separate H200 provisioning track should not block an A100/CPU engineering-agent pilot.

## Release acceptance

| Gate | Required evidence |
| --- | --- |
| Trusted deployment | Pinned upstream source, SBOM/provenance, container security, isolated authenticated private access, no public routes |
| Memory/identity | Paperclip restart keeps its task state; ACP identity and canonical memory are not duplicated or impersonated |
| Least privilege | Unauthorized project/GitHub write denied; MCP read-only fixture deny-write audit verified |
| One complete issue | Approved GitHub issue -> isolated agent work -> tests -> draft PR -> human review, with SHAs and logs |
| Fault tolerance | Force process restart; cancel and retry behavior correct, work not duplicated |
| Budget | Max one active task initially; token/time/iteration cap and explicit stop work |
| Model | Real authenticated A100 model response, no unapproved fallback; evidence of quality/latency |
| Promotion | CI passing, operator release approval, independently verified review; **no autonomous merge or deployment** |

**Stop rule:** after this one complete, bounded cycle passes, allow scheduled/heartbeat-based continuation on an explicit allowlist of GitHub issues, max concurrency and defined budget. Keep the canary isolated and require periodic human review. Never equate 'always-on' with unlimited LLM generation.

## Out of scope

Custom Paperclip clone; automatic researcher memory promotion; unrestricted web browsing; production Kubernetes tools; Docker socket access; broad GitHub repository credential; a new workflow runner; QPU provider privileged operations; a new scientific task scheduler; direct root access to H200.

## Operator staging

This document makes no deployment, secrets, image or cluster modifications. Before deployment, write a separate pilot topology PR with the pinned upstream image, per-workload PVC, NetworkPolicy, tested process/security policies, backup/restore, baseline metrics, termination, and rollback. Run initial sandbox smoke on a non-production host.
