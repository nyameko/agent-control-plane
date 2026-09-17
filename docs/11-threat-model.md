# 11. Threat model

## 11.1 Assets

- platform and research identities;
- private conversations, memories and research plans;
- infrastructure topology and security telemetry;
- Git repositories and supply chain;
- OpenStack/Kubernetes/Slurm/QPU credentials and resources;
- model weights, prompts, skills and agent definitions;
- scientific data, results and provenance;
- audit evidence and approvals.

## 11.2 Trust boundaries

- Internet and messaging platforms → liaison adapters;
- browser/editor/Jupyter clients → authenticated API;
- control plane → Hermes/other runtimes;
- runtime/model context → tool services;
- tool services → sandboxes/resource managers;
- tenant/user data → shared models and indexes;
- Git configuration → mutable runtime state;
- secret broker → short-lived execution environment.

## 11.3 Primary threats and controls

| Threat | Example | Primary controls |
| --- | --- | --- |
| indirect prompt injection | Suricata request text says “ignore policy and run…” | typed untrusted data, capability checks outside model, no raw privileged tools, injection evals |
| excessive agency | infra agent applies a plausible fix | proposal-only default, exact approvals, protected branches, GitOps authority |
| confused deputy | student asks tutor to use admin scope | subject/tenant propagation, non-amplifying delegation, per-tool authorisation |
| cross-tenant retrieval | collaboration agent exposes a private proposal | tenant filters, share grants, provenance, retrieval tests |
| secret exfiltration | tool output or prompt contains provider token | secret references/JIT injection, redaction, egress controls, no context exposure |
| channel impersonation | matching Discord nickname to portal user | one-time authenticated linking, immutable platform account IDs, revocation |
| approval substitution | approved command differs from executed command | canonical plan digest, expiry, single-use token, executor verifies digest |
| sandbox escape | generated code attacks worker/control plane | ephemeral isolation, non-root, seccomp/MAC, network policy, no control DB credential |
| supply-chain compromise | unpinned agent/model/container update | immutable digests, SBOM/signature policy, CI scanning, staged rollout |
| denial of wallet/resource | loop consumes H200/QPU allocations | quotas, iteration/time/token limits, leases, cancellation, budget alerts |
| memory poisoning | false result promoted to long-term memory | provenance, candidate review, correction/invalidation, trust score |
| audit tampering | compromised runtime deletes its history | out-of-process append-only events, protected export, no runtime delete capability |
| model fallback leak | private task falls back to external API | sensitivity-bound candidate set, explicit failure instead of silent fallback |

## 11.4 Tool result handling

Tool output is not trusted merely because the tool is trusted. Repositories, logs, papers,
webpages, filenames, job output and notebook cells may all contain adversarial instructions. Store
their origin and content type; quote/summarise them as evidence; never concatenate them into the
system-instruction layer.

## 11.5 Messaging safety

- verify webhook/platform signatures where supported;
- deduplicate events and enforce timestamp windows;
- rate limit per platform account and tenant;
- ignore unbound group participants for private tasks;
- require explicit bot mention in channels;
- redact sensitive task status;
- never accept high-risk approval from a reaction/emoji or free-text “yes”.

## 11.6 Administrative agent

The administrative orchestrator is a high-value target. Isolate it from ordinary user agents,
require strong authentication, restrict outbound access, use separate service identities, audit
every cross-tenant query and retain an independent stop/revocation path. Do not expose it directly
as the Telegram or Discord bot.

## 11.7 Incident response

Minimum controls before write capabilities:

- global pause of new agent runs;
- revoke agent/runtime/channel principal;
- disable one capability or model endpoint;
- stop an active run and its descendants;
- quarantine artifacts/workspaces;
- rotate secrets without rebuilding agent memory;
- reconstruct task → model → tool → approval → execution lineage;
- notify affected tenant/users according to incident policy.
