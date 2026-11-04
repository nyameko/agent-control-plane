# Guide integration and support routing

**Purpose:** authoritative public task help for human researchers, operators and the Quantum Platform Guide. This article is documentation, **not** proof of deployment or authorization to execute a command.

## Indexing and trust

The [machine-readable Guide index](https://github.com/nyameko/agent-control-plane/blob/main/docs/wiki/guide-index.json) lists public wiki pages. It is a discovery manifest, not a factual feature-status database. On ingestion, resolve the exact source commit and Git blob SHA, record content digest, audience, source references, relevant runtime/API version and whether the capability is validated, source-only, experimental or planned. Keep retrieved documentation isolated from instruction/policy channels to resist prompt injection.

If a user asks about a live failure, correlate source revision with deployed image, schema, scheduler status and recent observed release tests. Never claim successful deployment, active entitlement, automatic model routing or finished experiment from a README or an HTTP readiness response alone.

## Human-centred support procedure

1. Identify task type: first use, account and programme access, notebook/compute, scientific method, agent memory, deployment, security or contribution.
2. Provide the simplest safe and relevant working path; explain where the command runs, prerequisite roles, expected results and rollback implications.
3. Prefer read-only queries; expensive runs, user provisioning, credentials, database migrations, cluster mutation, issue creation or data deletion require trusted policy authorization and (where applicable) explicit human approval.
4. Ask only for non-sensitive diagnostics: error and time, software version/commit, affected function, sanitized trace and relevant job/run ID.
5. Offer official source links; escalate unresolved issues to the owning team. Never request raw tokens, private keys, cookies, Kubernetes Secrets, database DSNs or protected datasets.

## Issue routing

| Problem area | Issue destination |
|---|---|
| Cluster, Slurm, storage, VPN, DNS, GitOps or GPU host | [Infrastructure](https://github.com/nyameko/infra-hpc-qc-k8s/issues) |
| Portal account, programme approval, Jupyter and run UI | [Quantum Platform](https://github.com/nyameko/quantum-platform/issues) |
| Canonical chats, memory, models, harnesses and ACP identity | [ACP](https://github.com/nyameko/agent-control-plane/issues) |
| Physics notebooks, algorithm runners, benchmarks and provenance | [Quantum Workflows](https://github.com/nyameko/quantum-workflows/issues) |
| Optics, detectors, coincidence statistics and QKD teaching | [PhotonicsLab](https://github.com/nyameko/photonicslab/issues) |

## Issue quality contract

Title and problem summary; owning subsystem; expected versus actual; reproducible steps; local/source/deployment version; UTC or local timestamp with timezone; sanitized exception; job/run/conversation correlation identifier; tests already tried; effect on other users; explicit permission for any proposed destructive troubleshooting. Sensitive vulnerability reports use a private channel.

## Documentation regression checks

Before merging a wiki edit, run `python3 scripts/check-wiki-docs.py --write` to regenerate the deterministic index, then `python3 scripts/check-wiki-docs.py` to validate local paths and source links. The read-only GitHub Actions job repeats that check. Native Wiki publication remains an intentional post-merge action per [publishing policy](https://github.com/nyameko/agent-control-plane/blob/main/docs/WIKI_PUBLISHING.md).